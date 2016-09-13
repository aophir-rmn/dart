from dart.web import app

if __name__ == '__main__':

    # In stage/prod we use ELB certs to switch to https.
    # In local development (where we have auth.ssl_key_path key) we use a self signed certificate.
    # The reason for such use is that onelogin integration requires https connection to work properly.
    if (not app.config.get('auth').get('use_auth')) or (app.config['auth'].get('ssl_key_path') is None):
        app.run(host=app.config['dart_host'], port=app.config['dart_port'], use_reloader=False)
    else:
        context = (app.config.get('auth').get('ssl_cert_path'), app.config.get('auth').get('ssl_key_path'))
        app.run(host=app.config['dart_host'], port=app.config['dart_port'], use_reloader=False, ssl_context=context)


