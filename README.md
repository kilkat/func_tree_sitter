# Call Tree Analyzer

Tree-sitter를 이용한 다중 언어 호출 트리 분석 도구

## 개요

Call Tree Analyzer는 소스 코드의 함수 호출 관계를 분석하여 호출 트리를 생성하는 도구입니다. Tree-sitter 파서를 사용하여 C, Python, JavaScript 코드를 정확하게 분석합니다.

## 지원 언어

- **C** (`.c`, `.h`)
- **Python** (`.py`)
- **JavaScript** (`.js`, `.jsx`, `.ts`, `.tsx`)

## 설치 및 환경 설정

### 1. Python 가상환경 생성

```bash
py -3.10 -m venv .venv
```

### 2. 가상환경 활성화

```bash
# Windows
.\.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate
```

### 3. 의존성 설치

```bash
# uv 사용 (권장)
uv pip install -r requirements.txt

# 또는 pip 사용
pip install -r requirements.txt
```

### 4. 개발 모드 설치 (선택사항)

```bash
pip install -e .
```

## 사용법

### 기본 사용법

```bash
# 프로젝트 분석
python -m call_tree_analyzer /path/to/project

# 단일 파일 분석
python -m call_tree_analyzer /path/to/file.py --single-file
```

### CLI 옵션

#### 기본 인자

- `path` (필수): 분석할 프로젝트 디렉터리 또는 파일 경로

#### 출력 관련 옵션

- `--output, -o`: 결과를 파일로 저장할 경로
- `--format, -f`: 출력 형식 (`json` 또는 `text`, 기본값: `json`)

#### 분석 모드 옵션

- `--single-file`: 단일 파일만 분석
- `--workers, -w`: 병렬 처리 워커 수 (기본값: 4)

#### 분석 결과 옵션

- `--stats`: 상세한 통계 정보 포함
- `--hotspots`: 핫스팟 분석 결과 포함

#### 로깅 및 디버깅 옵션

- `--log-level`: 로그 레벨 (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `--log-file`: 로그 파일 경로
- `--quiet, -q`: 최소한의 출력만 표시

### 사용 예시

#### 기본 분석

```bash
# JSON 형태로 출력
python -m call_tree_analyzer ./my_project

# 텍스트 형태로 출력
python -m call_tree_analyzer ./my_project --format text
```

#### 결과를 파일로 저장

```bash
# JSON 파일로 저장
python -m call_tree_analyzer ./my_project --output analysis.json

# 텍스트 파일로 저장
python -m call_tree_analyzer ./my_project --format text --output report.txt
```

#### 통계 및 핫스팟 분석

```bash
# 통계 정보 포함
python -m call_tree_analyzer ./my_project --stats --format text

# 핫스팟 분석 결과 포함
python -m call_tree_analyzer ./my_project --hotspots --format text

# 모든 분석 결과 포함
python -m call_tree_analyzer ./my_project --stats --hotspots --format text
```

#### 성능 최적화

```bash
# 병렬 처리 워커 수 조정 (대용량 프로젝트)
python -m call_tree_analyzer ./large_project --workers 8

# 조용한 모드 (진행상황 숨김)
python -m call_tree_analyzer ./my_project --quiet --output result.json
```

#### 디버깅

```bash
# 상세 로그 출력
python -m call_tree_analyzer ./my_project --log-level DEBUG

# 로그를 파일로 저장
python -m call_tree_analyzer ./my_project --log-file analysis.log
```

#### 종합 분석 예시

```bash
python -m call_tree_analyzer ./my_project \
    --output comprehensive_analysis.json \
    --stats \
    --hotspots \
    --workers 6 \
    --log-file analysis.log \
    --log-level INFO
```

## 출력 형식

### JSON 출력 예시

```json
{
  "functions": {
    "/path/to/file.py::main": {
      "name": "main",
      "file": "/path/to/file.py",
      "line": 10,
      "column": 0,
      "calls": [
        {
          "name": "process_data",
          "line": 12,
          "column": 4
        }
      ]
    }
  },
  "statistics": {
    "total_functions": 15,
    "total_calls": 42,
    "avg_calls_per_function": 2.8
  },
  "hotspots": {
    "most_called_functions": ["helper_func", "utils_process"],
    "orphaned_functions": ["old_unused_func"]
  }
}
```

### 텍스트 출력 예시

```
=== Call Tree Analysis ===

/path/to/file.py::main (/path/to/file.py:10)
  └─ process_data (line 12)
  └─ cleanup (line 15)

/path/to/file.py::process_data (/path/to/file.py:20)
  └─ helper_func (line 22)
  └─ validate_input (line 24)

=== Statistics ===
total_functions: 15
total_calls: 42
avg_calls_per_function: 2.80

=== Hotspots ===
Most Called Functions:
  - helper_func
  - utils_process

Orphaned Functions:
  - old_unused_func
```

## 주요 기능

### 🔍 다중 언어 지원

- Tree-sitter 파서를 이용한 정확한 구문 분석
- C, Python, JavaScript 지원

### ⚡ 성능 최적화

- 병렬 처리를 통한 빠른 분석
- 대용량 프로젝트 지원

### 📊 상세한 분석 결과

- 함수 호출 관계 시각화
- 복잡도 메트릭 계산
- 핫스팟 분석 (가장 많이 호출되는 함수 등)

### 🛠️ 유연한 출력 형식

- JSON: 프로그래밍 처리에 적합
- 텍스트: 사람이 읽기 쉬운 형태

### 🔧 설정 가능한 분석 옵션

- 무시할 파일/디렉터리 패턴 설정
- 내장 함수 호출 포함/제외
- 익명 함수 처리 옵션

## 프로젝트 구조

```
func_tree_sitter/
├── src/
│   └── call_tree_analyzer/
│       ├── __init__.py
│       ├── __main__.py          # 모듈 진입점
│       ├── cli.py               # CLI 인터페이스
│       ├── config.py            # 설정 관리
│       ├── analyzer.py          # 메인 분석 로직
│       ├── utils.py             # 유틸리티 함수
│       ├── models/              # 데이터 모델
│       │   ├── __init__.py
│       │   ├── function.py      # 함수 관련 모델
│       │   ├── call_tree.py     # 호출 트리 모델
│       │   └── project.py       # 프로젝트 관련 모델
│       └── parsers/             # 언어별 파서
│           ├── __init__.py
│           ├── base.py          # 추상 파서 클래스
│           ├── c_parser.py      # C 언어 파서
│           ├── python_parser.py # Python 파서
│           └── javascript_parser.py # JavaScript 파서
├── requirements.txt             # 의존성
└── README.md
```

## 개발자를 위한 정보

### 새로운 언어 지원 추가

1. `parsers/` 디렉터리에 새 파서 클래스 생성
2. `BaseParser`를 상속하여 언어별 메서드 구현
3. `parsers/__init__.py`의 `PARSER_CLASSES`에 추가
4. `config.py`의 `LANGUAGE_CONFIG`에 언어 설정 추가

### 코드 포맷팅

```bash
black src/
```

## 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 문제 해결

### 일반적인 문제들

#### `tree_sitter_languages` 설치 오류

```bash
# 최신 버전 설치
pip install --upgrade tree-sitter-languages
```

#### 메모리 부족 오류 (대용량 프로젝트)

```bash
# 워커 수 줄이기
python -m call_tree_analyzer ./project --workers 2
```

#### 권한 오류

```bash
# 읽기 권한이 있는 디렉터리인지 확인
ls -la /path/to/project
```
