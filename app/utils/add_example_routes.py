def register_example_plugin(app):
    """
    Register the example plugin with the application
    """
    from app.blueprints.example.plugin import ExamplePlugin
    example_plugin = ExamplePlugin()
    example_plugin.init_app(app)
