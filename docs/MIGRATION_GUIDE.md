# Django 마이그레이션 문제 해결 가이드

## 📋 질문과 답변

### Q1: `clean_django_tables.py`를 다른 사람이 사용해도 될까?

**A: 주의해서 사용해야 합니다.**

- ✅ **사용 가능한 경우:**

  - 개발 환경에서 테스트 중일 때
  - 데이터 손실이 문제되지 않을 때
  - 모든 팀원이 동의했을 때

- ❌ **사용하면 안 되는 경우:**
  - 프로덕션 환경
  - 중요한 데이터가 있는 경우
  - 다른 사람이 작업 중일 때

**권장 사항:** `fix_migration_history.py`를 먼저 시도하세요. (데이터 유지)

---

### Q2: `makemigrations`가 자동으로 변동사항을 찾아서 마이그레이션하는 것 아닌지?

**A: 부분적으로 맞습니다.**

Django 마이그레이션은 두 단계로 나뉩니다:

1. **`makemigrations`**: 모델 변경사항을 감지하여 마이그레이션 **파일**을 생성

   - 모델 파일(`models.py`)의 변경사항을 감지
   - 마이그레이션 파일(`migrations/0001_initial.py` 등)을 생성
   - **데이터베이스는 변경하지 않음**

2. **`migrate`**: 마이그레이션 파일을 실제로 데이터베이스에 **적용**
   - 생성된 마이그레이션 파일을 실행
   - 데이터베이스 스키마를 변경
   - `django_migrations` 테이블에 기록

**정상적인 흐름:**

```bash
# 1. 모델 변경 (models.py 수정)
# 2. 마이그레이션 파일 생성
python manage.py makemigrations

# 3. 데이터베이스에 적용
python manage.py migrate
```

---

### Q3: 왜 이런 오류가 발생했는지?

**A: 마이그레이션 히스토리 불일치 때문입니다.**

**문제 상황:**

```
데이터베이스 상태:
  ✅ admin.0001_initial (이미 적용됨)
  ❌ users.0001_initial (적용 안 됨)

의존성 관계:
  admin.0001_initial → users.0001_initial (의존)
```

**발생 원인:**

1. 다른 사람이 `python manage.py migrate`를 실행했을 때
2. `admin` 앱의 마이그레이션이 먼저 적용됨
3. 하지만 `users` 앱의 마이그레이션이 적용되지 않았거나 실패함
4. 결과적으로 `django_migrations` 테이블에 불일치한 기록이 남음

**오류 메시지:**

```
InconsistentMigrationHistory:
Migration admin.0001_initial is applied before its dependency
users.0001_initial on database 'default'.
```

---

## 🔧 해결 방법

### 방법 1: 마이그레이션 히스토리만 수정 (권장, 데이터 유지)

```bash
# 1. 마이그레이션 히스토리 수정
python fix_migration_history.py

# 2. 마이그레이션 적용
python manage.py migrate --fake-initial
python manage.py migrate
```

**장점:**

- ✅ 기존 데이터 유지
- ✅ 안전함
- ✅ 다른 사람과 충돌 없음

---

### 방법 2: 모든 Django 테이블 삭제 (주의 필요)

```bash
# 1. 모든 Django 테이블 삭제
python clean_django_tables.py

# 2. 마이그레이션 재적용
python manage.py migrate
```

**주의사항:**

- ⚠️ **모든 데이터가 삭제됩니다**
- ⚠️ 개발 환경에서만 사용하세요
- ⚠️ 다른 사람과 협의 후 사용하세요

---

### 방법 3: 수동으로 마이그레이션 히스토리 수정

데이터베이스에 직접 접속하여:

```sql
-- 문제가 되는 레코드 삭제
DELETE FROM django_migrations
WHERE app = 'admin' AND name = '0001_initial';

-- 또는 모든 마이그레이션 히스토리 초기화
DELETE FROM django_migrations;
```

그 후:

```bash
python manage.py migrate --fake-initial
python manage.py migrate
```

---

## 📝 예방 방법

### 1. 팀원과 마이그레이션 파일 공유

```bash
# 마이그레이션 파일은 Git에 커밋해야 함
git add apps/*/migrations/
git commit -m "Add migrations"
git push
```

### 2. 마이그레이션 순서 확인

```bash
# 마이그레이션 상태 확인
python manage.py showmigrations
```

### 3. 충돌 방지

- 마이그레이션 파일을 수정하지 말 것
- 다른 사람의 마이그레이션을 pull 받은 후 `migrate` 실행
- 마이그레이션 충돌 시 팀원과 협의

---

## 🚨 주의사항

1. **프로덕션 환경에서는 절대 `clean_django_tables.py` 사용 금지**
2. **데이터 백업 후 작업**
3. **팀원과 협의 후 실행**
4. **마이그레이션 파일은 절대 수정하지 말 것**
