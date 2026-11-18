import flask.blueprints

_orig_setup_init = flask.blueprints.BlueprintSetupState.__init__

def _custom_setup_init(self, blueprint, app, options, first_registration):
    _orig_setup_init(self, blueprint, app, options, first_registration)
    opt_prefix = options.get("url_prefix")
    bp_prefix = blueprint.url_prefix
    if opt_prefix and bp_prefix:
        self.url_prefix = opt_prefix.rstrip("/") + "/" + bp_prefix.lstrip("/")

flask.blueprints.BlueprintSetupState.__init__ = _custom_setup_init
