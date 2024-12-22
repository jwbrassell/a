"""Document utility functions."""
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from flask import current_app
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.documents import Document, DocumentCache, DocumentCategory

# Try to import pdfkit, but don't fail if it's not available
try:
    import pdfkit
    PDFKIT_AVAILABLE = True
except ImportError:
    PDFKIT_AVAILABLE = False

def get_or_create_cache(document: Document, format: str) -> Optional[bytes]:
    """Get cached document content or create new cache."""
    # Check for existing cache
    cache = DocumentCache.query.filter_by(
        document_id=document.id,
        format=format
    ).first()

    if cache and cache.content:
        return cache.content

    # Generate new cache
    content = None
    if format == 'pdf' and PDFKIT_AVAILABLE:
        try:
            # Convert HTML to PDF
            content = pdfkit.from_string(document.content, False)
        except Exception as e:
            current_app.logger.error(f"PDF generation failed: {e}")
    elif format == 'docx':
        try:
            # Simple HTML to DOCX conversion (placeholder)
            content = document.content.encode('utf-8')
        except Exception as e:
            current_app.logger.error(f"DOCX generation failed: {e}")

    if content:
        # Store in cache
        cache = DocumentCache(
            document_id=document.id,
            format=format,
            content=content
        )
        try:
            db.session.add(cache)
            db.session.commit()
        except Exception as e:
            current_app.logger.error(f"Cache storage failed: {e}")
            db.session.rollback()

    return content

def bulk_categorize(document_ids: List[int], category_id: int) -> bool:
    """Categorize multiple documents."""
    try:
        # Verify category exists
        category = DocumentCategory.query.get(category_id)
        if not category:
            return False

        # Update documents
        Document.query.filter(Document.id.in_(document_ids)).update(
            {Document.category_id: category_id},
            synchronize_session=False
        )
        db.session.commit()
        return True
    except Exception as e:
        current_app.logger.error(f"Bulk categorization failed: {e}")
        db.session.rollback()
        return False

def bulk_delete(document_ids: List[int]) -> bool:
    """Delete multiple documents."""
    try:
        # Delete associated files first
        documents = Document.query.filter(Document.id.in_(document_ids)).all()
        for doc in documents:
            file_path = os.path.join(
                current_app.config['UPLOAD_FOLDER'],
                str(doc.id)
            )
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception as e:
                    current_app.logger.error(f"File deletion failed for document {doc.id}: {e}")

        # Delete documents from database
        Document.query.filter(Document.id.in_(document_ids)).delete(
            synchronize_session=False
        )
        db.session.commit()
        return True
    except Exception as e:
        current_app.logger.error(f"Bulk deletion failed: {e}")
        db.session.rollback()
        return False

def save_document_file(file, document_id: int) -> Optional[str]:
    """Save uploaded document file."""
    if not file:
        return None
        
    filename = secure_filename(file.filename)
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(document_id))
    os.makedirs(upload_dir, exist_ok=True)
    
    file_path = os.path.join(upload_dir, filename)
    file.save(file_path)
    
    return filename

def get_document_path(document_id: int, filename: str) -> str:
    """Get full path to document file."""
    return os.path.join(
        current_app.config['UPLOAD_FOLDER'],
        str(document_id),
        filename
    )

def delete_document_file(document_id: int, filename: str) -> bool:
    """Delete document file."""
    try:
        file_path = get_document_path(document_id, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True
    except Exception as e:
        current_app.logger.error(f"Failed to delete file: {e}")
    return False

def get_document_metadata(document_id: int) -> Dict[str, Any]:
    """Get document metadata."""
    metadata_path = os.path.join(
        current_app.config['UPLOAD_FOLDER'],
        str(document_id),
        'metadata.json'
    )
    
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            current_app.logger.error(f"Failed to read metadata: {e}")
    
    return {}

def save_document_metadata(document_id: int, metadata: Dict[str, Any]) -> bool:
    """Save document metadata."""
    try:
        metadata_dir = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            str(document_id)
        )
        os.makedirs(metadata_dir, exist_ok=True)
        
        metadata_path = os.path.join(metadata_dir, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to save metadata: {e}")
        return False

def get_document_versions(document_id: int) -> List[Dict[str, Any]]:
    """Get document version history."""
    versions_path = os.path.join(
        current_app.config['UPLOAD_FOLDER'],
        str(document_id),
        'versions.json'
    )
    
    if os.path.exists(versions_path):
        try:
            with open(versions_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            current_app.logger.error(f"Failed to read versions: {e}")
    
    return []

def add_document_version(document_id: int, version_info: Dict[str, Any]) -> bool:
    """Add new document version."""
    try:
        versions = get_document_versions(document_id)
        versions.append({
            **version_info,
            'timestamp': datetime.utcnow().isoformat()
        })
        
        versions_dir = os.path.join(
            current_app.config['UPLOAD_FOLDER'],
            str(document_id)
        )
        os.makedirs(versions_dir, exist_ok=True)
        
        versions_path = os.path.join(versions_dir, 'versions.json')
        with open(versions_path, 'w') as f:
            json.dump(versions, f, indent=2)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to add version: {e}")
        return False

def get_document_stats(document_id: int) -> Dict[str, Any]:
    """Get document statistics."""
    try:
        stats = {
            'versions': len(get_document_versions(document_id)),
            'metadata': bool(get_document_metadata(document_id))
        }
        
        # Get file info if exists
        doc_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], str(document_id))
        if os.path.exists(doc_dir):
            files = [f for f in os.listdir(doc_dir) if os.path.isfile(os.path.join(doc_dir, f))]
            stats.update({
                'files': len(files),
                'total_size': sum(os.path.getsize(os.path.join(doc_dir, f)) for f in files)
            })
        
        return stats
    except Exception as e:
        current_app.logger.error(f"Failed to get stats: {e}")
        return {}
