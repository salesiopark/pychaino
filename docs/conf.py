import os
import sys
sys.path.insert(0, os.path.abspath('..'))
sys.path.insert(0, os.path.abspath('../src'))

project = 'chaino'
copyright = '2025, Jang-Hyun Park'
author = 'Jang-Hyun Park'

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.viewcode',
    'sphinx.ext.napoleon',
    'sphinx.ext.githubpages',
]

html_theme = 'sphinx_rtd_theme'
html_static_path = []

# autodoc 설정 강화
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'show-inheritance': True,
    'inherited-members': True,  # 상속된 메서드도 포함
    'exclude-members': '__weakref__'
}

# Mock imports for missing modules (MicroPython 관련)
autodoc_mock_imports = ['machine', 'binascii']

# Napoleon 설정 (Google/NumPy style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = False


'''
# 아래 코드는 docstring에 :exclude-from-docs:가 포함된 함수를 문서화에서 제외
# conf.py에 이 코드를 추가하면, 해당 태그가 있는 함수는 자동으로 제외됨
def skip_member(app, what, name, obj, skip, options):
    # docstring에서 ':exclude-from-docs:' 태그 확인
    if obj.__doc__ and ':exclude-from-docs:' in obj.__doc__:
        return True  # 문서화에서 제외
    return skip

def setup(app):
    app.connect("autodoc-skip-member", skip_member)
'''

import importlib

# Chaino 클래스를 임포트하여 모듈 경로를 정확하게 비교할 수 있도록 합니다.
# 실제 프로젝트 구조에 맞게 경로를 확인해주세요.
try:
    from chaino.chaino import Chaino 
except ImportError:
    # 경로 문제가 발생할 경우를 대비한 예외 처리
    Chaino = None




def record_current_class(app, what, name, obj, options, lines):
    """
    'autodoc-process-docstring' 이벤트 핸들러.
    현재 문서화 중인 클래스의 전체 경로 이름을 환경 변수에 저장합니다.
    """
    if what == 'class':
        # app.env.temp_data는 빌드 중에 임시 데이터를 저장하는 안전한 공간입니다.
        app.env.temp_data['current_autodoc_class'] = name

def autodoc_skip_member_handler(app, what, name, obj, skip, options):
    """
    'autodoc-skip-member' 이벤트 핸들러.
    여러 조건을 확인하여 멤버를 문서에서 제외시킵니다.
    """
    # --- 조건 1: Docstring에 ':exclude-from-docs:' 태그가 있는지 확인 ---
    if hasattr(obj, '__doc__') and isinstance(obj.__doc__, str):
        if ':exclude-from-docs:' in obj.__doc__:
            return True

    # --- 조건 2: Chaino를 상속받는 모든 자식 클래스에서 Chaino 멤버 제외 ---
    # Chaino 클래스를 임포트하지 못했다면 이 로직을 건너뜁니다.
    if not Chaino:
        return skip

    # 현재 처리 중인 클래스의 전체 경로를 가져옵니다.
    current_class_path = app.env.temp_data.get('current_autodoc_class')
    if not current_class_path:
        return skip

    try:
        # 클래스 경로 문자열로부터 실제 클래스 객체를 동적으로 가져옵니다.
        # 예: 'chaino.hana.Hana' -> Hana 클래스 객체
        module_name, class_name = current_class_path.rsplit('.', 1)
        module = importlib.import_module(module_name)
        current_class_obj = getattr(module, class_name)
    except (ImportError, AttributeError, ValueError):
        # 클래스를 가져오지 못하면 기본 동작에 맡깁니다.
        return skip

    # 현재 클래스가 Chaino의 자식 클래스인지, 그리고 Chaino 자신이 아닌지 확인
    is_subclass_of_chaino = issubclass(current_class_obj, Chaino)
    is_chaino_itself = (current_class_obj is Chaino)

    # 현재 클래스가 Chaino의 자식이면서 Chaino 자신이 아니고,
    # 제외하려는 멤버(obj)의 원 소속 모듈이 Chaino의 모듈과 같다면 제외합니다.
    if is_subclass_of_chaino and not is_chaino_itself and \
       hasattr(obj, '__module__') and obj.__module__ == Chaino.__module__:
        return True
    
    # 위의 어떤 조건에도 해당하지 않으면, Sphinx의 원래 skip 결정에 따릅니다.
    return skip

def setup(app):
    # 'autodoc-process-docstring' 이벤트에 핸들러를 연결하여 현재 클래스 이름을 기록합니다.
    app.connect("autodoc-process-docstring", record_current_class)
    
    # 'autodoc-skip-member' 이벤트에 주 제외 로직 핸들러를 연결합니다.
    app.connect("autodoc-skip-member", autodoc_skip_member_handler)