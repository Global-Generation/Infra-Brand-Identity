"""Build gg-id/account-menu/gg-account-menu.css: the styles of the GG account menu (GGAccountMenu).

The look of the menu is the look of the kit chip and menu that AKB uses (.gid-chip, .gid-menu, ...). So the CSS is not written twice: the blocks
below are copied VERBATIM from gg-id/gg-id.css (tokens of both themes, resets, icons, avatar, chip and menu), then src/account_menu/local.css
adds what the kit does not have (the services list, sections, the narrow-screen chip). A change of the look = a change of gg-id.css, then
`python3 src/build_account_menu.py`; the check (src/check_account_menu.py) fails when the committed file differs from what this script makes.

Run:   python3 src/build_account_menu.py            write gg-id/account-menu/gg-account-menu.css
       python3 src/build_account_menu.py --check    do not write, exit 1 when the file is not what the kit makes (also: versions agree)
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
KIT = os.path.join(ROOT, 'gg-id')
OUT_DIR = os.path.join(KIT, 'account-menu')
OUT = os.path.join(OUT_DIR, 'gg-account-menu.css')
JS = os.path.join(OUT_DIR, 'gg-account-menu.js')
LOCAL = os.path.join(HERE, 'account_menu', 'local.css')


def read(path):
    with open(path, encoding='utf-8') as f:
        return f.read()


def between(css, first, last, what):
    """From the start of the line that begins with `first` to the end of the line that begins with `last` (both lines inclusive)."""
    a = css.find('\n' + first)
    assert a >= 0, f'gg-id.css: no line starting with {first!r} ({what}); the kit moved the block, update src/build_account_menu.py'
    a += 1
    b = css.find('\n' + last, a - 1)      # a - 1: the first and the last line may be one line
    assert b >= 0, f'gg-id.css: no line starting with {last!r} after {first!r} ({what})'
    b += 1
    end = css.find('\n', b)
    return css[a:end if end >= 0 else len(css)]


def kit_blocks(css):
    """[(title, text)]: the pieces of gg-id.css the account menu needs, byte for byte."""
    tokens_a = css.index('/* ---------- токены: светлая тема ---------- */')
    tokens_b = css.index('/* ---------- страница и оболочка ---------- */')
    return [
        ('tokens: light theme, dark theme, dark by the system', css[tokens_a:tokens_b].rstrip('\n')),
        ('box-sizing', between(css, '.gid,.gid *,.gid *::before', '.gid,.gid *,.gid *::before', 'box-sizing')),
        ('resets and [hidden]', between(css, '/* сбросы с нулевой специфичностью', '.gid [hidden],.gid-kit [hidden]', 'resets')),
        ('no break inside the domain of an e-mail', between(css, '.gid-nowrap{', '.gid-nowrap{', 'nowrap')),
        ('icons', between(css, '.gid-ic{', '.gid-ic--fill{', 'icons')),
        ('avatar', between(css, '/* аватар: инициалы белым', ':is(.gid,.gid-kit) .gid-avatar--xs{', 'avatar')),
        ('account chip and menu', between(css, '/* аккаунт в шапке сервиса', '.gid-menu-sep{', 'chip and menu')),
    ]


def make():
    css = read(os.path.join(KIT, 'gg-id.css'))
    version = read(os.path.join(KIT, 'VERSION')).strip()
    head = (
        f'/* GG account menu: styles of the account chip and its dropdown. Kit version {version} (gg-id/VERSION).\n'
        '   GENERATED, do not edit by hand: python3 src/build_account_menu.py (Global-Generation/Infra-Brand-Identity).\n'
        '   The blocks marked "kit" are copied byte for byte from gg-id/gg-id.css, so the menu looks exactly like the kit chip and menu of AKB;\n'
        '   the last block is src/account_menu/local.css (services list, sections, narrow screen). A change of the look is a PR to the kit.\n'
        '   No @font-face: the page loads Montserrat itself (gg-id/fonts/); without it the menu falls back to system-ui. No external addresses. */\n'
    )
    parts = [head]
    for title, text in kit_blocks(css):
        parts.append(f'/* kit: {title} */\n{text}\n')
    parts.append(read(LOCAL).rstrip('\n') + '\n')
    return '\n'.join(parts)


def versions_agree():
    """gg-id/VERSION, the version in the first line of the CSS and the JS (header and VERSION constant) are one string."""
    version = read(os.path.join(KIT, 'VERSION')).strip()
    js = read(JS)
    bad = []
    if re.findall(r"var VERSION = '([^']+)'", js) != [version]:
        bad.append(f'gg-account-menu.js: var VERSION must be {version}')
    if f'Kit version {version} (gg-id/VERSION)' not in js.split('\n', 1)[0]:
        bad.append(f'gg-account-menu.js: the first line must say "Kit version {version} (gg-id/VERSION)"')
    return bad


if __name__ == '__main__':
    out = make()
    problems = versions_agree()
    if '--check' in sys.argv:
        have = read(OUT) if os.path.exists(OUT) else ''
        if have != out:
            problems.append('gg-account-menu.css is not what the kit makes: run python3 src/build_account_menu.py')
        if problems:
            print('\n'.join(problems))
            sys.exit(1)
        print('ok gg-account-menu.css is in step with gg-id.css | version', read(os.path.join(KIT, 'VERSION')).strip())
    else:
        if problems:
            print('\n'.join(problems))
            sys.exit(1)
        os.makedirs(OUT_DIR, exist_ok=True)
        if not os.path.exists(OUT) or read(OUT) != out:
            with open(OUT, 'w', encoding='utf-8') as f:
                f.write(out)
        print('ok gg-account-menu.css', f'{len(out) / 1024:.1f} KB', '| version', read(os.path.join(KIT, 'VERSION')).strip())
