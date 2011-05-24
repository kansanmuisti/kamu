import settings
from django_assets import Bundle, register

js_filters = 'jsmin' if not settings.JS_DEBUG else None
js = Bundle('js/jquery-1.5.1.js', 'js/jquery.cookie.js',
            'js/jquery-ui-1.8.11.custom.js', 'js/jquery-ui-combobox.js',
            'js/jquery.example.js', 'js/jquery.tooltip.js',
            'js/jquery.jnotify.js', 'js/ui-uservote.js',
            'js/utils.js',
            filters=js_filters, output='gen/packed.js')
register('js_base', js)

raphael = Bundle('js/raphael.js', filters=js_filters, output='gen/raphael.js')
register('raphael', raphael)

css = Bundle(Bundle('css/kamu.css', filters='less'),
             Bundle('css/jquery-ui-1.8.1.custom.css', filters='cssrewrite'),
             filters='cssutils', output='gen/packed.css')
register('css_base', css)
