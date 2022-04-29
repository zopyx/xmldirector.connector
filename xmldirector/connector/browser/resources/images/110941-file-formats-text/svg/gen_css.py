import os

for name in os.listdir('.'):
    if not name.endswith('.svg'):
        continue

    base, other = name.split('-', 1)
    print('a.type-file[href*=".{}"]:before {}'.format(base, '{'))
    print(
        f'    background-image: url(++resource++xmldirector.plonecore/images/110940-file-formats-text/svg/{name}) !important;'
    )

    print('}')
    print()

