"""Development server."""

from app import create_app

if __name__ == '__main__':
    app = create_app('development')
    print("Starting development server at http://localhost:5000")
    app.run(host='localhost', port=5000, debug=True)
