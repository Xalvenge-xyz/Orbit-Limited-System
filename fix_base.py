import pathlib
p = pathlib.Path('templates/base.html')
s = p.read_text()
s = s.replace('<html lang="en" data-theme="dark">\n  <meta charset="UTF-8" />',
              '<html lang="en" data-theme="dark">\n<head>\n  <meta charset="UTF-8" />')
# close head before BODY_PLACEHOLDER
s = s.replace('  {% block extra_css %}{% endblock %}\nBODY_PLACEHOLDER',
              '  {% block extra_css %}{% endblock %}\n</head>\n<body class="font-sans min-h-screen flex flex-col selection:bg-nasa-cyan selection:text-black">\nBODY_PLACEHOLDER')
p.write_text(s)
print('done')
