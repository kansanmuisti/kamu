from django_assets import Bundle, register

js = Bundle('js/jquery-1.5.1.js', 'js/jquery.cookie.js',
            'js/jquery-ui-1.8.11.custom.js', 'js/jquery-ui-combobox.js',
            'js/jquery.example.js', 'js/jquery.tooltip.js',
            'js/jquery.jnotify.js', filters='jsmin', output='gen/packed.js')
register('js_base', js)

css = Bundle(Bundle('css/kamu.css', filters='less'),
             Bundle('css/jquery-ui-1.8.1.custom.css', filters='cssrewrite'),
             filters='cssutils', output='gen/packed.css')
register('css_base', css)
