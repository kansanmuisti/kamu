import settings
from django_assets import Bundle, register

debug=settings.JS_DEBUG
js = Bundle('js/jquery-1.5.1.js', 'js/jquery.cookie.js',
            'js/jquery-ui-1.8.11.custom.js', 'js/jquery-ui-combobox.js',
            'js/jquery.example.js', 'js/jquery.tooltip.js',
            'js/jquery.jnotify.js', 'js/ui-uservote.js',
            filters='jsmin' if debug else None, output='gen/packed.js')
register('js_base', js)

css = Bundle(Bundle('css/kamu.css', filters='less'),
             Bundle('css/jquery-ui-1.8.1.custom.css', filters='cssrewrite'),
             filters='cssutils', output='gen/packed.css')
register('css_base', css)
