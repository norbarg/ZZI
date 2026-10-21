"""DevBridge Solutions: навчальна перевірка декларативної конфігурації безпеки.
Запуск: python security_controls_checker.py
       python security_controls_checker.py --config system_config.json --checklist control_checklist.json
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

BASE = Path(__file__).resolve().parent


def get(config, *keys, default=None):
    value = config
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


def check_mfa(c):
    users = get(c, 'identity', 'users', default=[])
    if not users:
        return False, 'Немає записів користувачів для перевірки'
    bad = [u.get('id', '?') for u in users if not u.get('mfa_enabled')]
    return not bad and get(c, 'identity', 'mfa_policy_all_180') is True, ('Політика MFA для 180 осіб декларована; усі тестові записи з MFA' if not bad and get(c, 'identity', 'mfa_policy_all_180') is True else 'Політика MFA не задана або без MFA: ' + ', '.join(bad))


def check_admin_fido(c):
    users = get(c, 'identity', 'users', default=[])
    privileged = [u for u in users if u.get('role') in ('DevOps', 'Security', 'SysAdmin')]
    if not privileged:
        return False, 'Немає записів привілейованих користувачів'
    bad = [u.get('id', '?') for u in privileged if u.get('mfa_method') != 'FIDO2']
    return not bad, ('Усі привілейовані записи використовують FIDO2' if not bad else 'Не FIDO2: '+', '.join(bad))


def check_project_isolation(c):
    """ВЛАСНА перевірка для брифу №3: ізоляція всіх восьми клієнтських проєктів."""
    projects = get(c, 'gitlab', 'projects', default=[])
    ids = [p.get('id') for p in projects]
    if len(projects) != 8 or len(set(ids)) != 8 or set(ids) != {f'P{i}' for i in range(1, 9)}:
        return False, 'Очікується вісім унікальних проєктів P1–P8'
    bad = [p['id'] for p in projects if not (p.get('isolated') is True and p.get('cross_project_access') is False)]
    return not bad, ('Проєкти P1–P8 ізольовані' if not bad else 'Порушення ізоляції: ' + ', '.join(bad))


def check_cicd_secrets(c):
    """ВЛАСНА перевірка для брифу №3: захист секретів GitLab CI/CD."""
    runners = get(c, 'cicd', 'runners', default=[])
    if not runners:
        return False, 'Немає даних про CI/CD runner'
    bad = [r.get('id', '?') for r in runners if not (r.get('protected') is True and r.get('isolated') is True and r.get('long_lived_secrets') is False)]
    return not bad, ('Runner ізольовані та не містять довгострокових секретів' if not bad else 'Небезпечні runner: '+', '.join(bad))


def check_tls(c):
    return get(c, 'crypto', 'tls_min_version') == '1.3', 'Мінімальна версія TLS: ' + str(get(c, 'crypto', 'tls_min_version', default='невідома'))


def check_encryption(c):
    algo = get(c, 'crypto', 'data_encryption')
    kms = get(c, 'crypto', 'kms_enabled')
    ok = algo == 'AES-256-GCM' and kms is True
    return ok, f'Шифрування={algo}, KMS={kms}'


def check_backup(c):
    b = get(c, 'backup', default={})
    ok = b.get('encrypted') is True and b.get('immutable') is True and b.get('last_restore_test_days_ago', 9999) <= 90 and b.get('gitlab_interval_minutes', 9999) <= 60
    return ok, f"Encrypted={b.get('encrypted')}, immutable={b.get('immutable')}, тест={b.get('last_restore_test_days_ago')} днів, GitLab interval={b.get('gitlab_interval_minutes')} хв"


def check_logging(c):
    l = get(c, 'monitoring', default={})
    required = {'gitlab', 'iam', 'cicd', 'vpn', 'firewall'}
    sources = set(l.get('sources', []))
    ok = l.get('centralized') is True and l.get('retention_days', 0) >= 180 and required <= sources
    return ok, 'SIEM=' + str(l.get('centralized')) + '; retention=' + str(l.get('retention_days')) + '; відсутні джерела=' + ','.join(sorted(required-sources))

# Registry Pattern з методички; ISO-посилання — прив'язка до обраних контролів.
CHECK_REGISTRY = {
    'ID-01': {'name':'MFA для всіх користувачів', 'standard':'ISO/IEC 27001:2022 A.8.5', 'severity':'HIGH', 'risk':'T1', 'recommendation':'Увімкнути MFA для всіх облікових записів.', 'fn':check_mfa},
    'ID-02': {'name':'FIDO2 для привілейованих ролей', 'standard':'ISO/IEC 27001:2022 A.8.5', 'severity':'HIGH', 'risk':'T1', 'recommendation':'Перевести DevOps/Security/SysAdmin на FIDO2.', 'fn':check_admin_fido},
    'DS-01': {'name':'Ізоляція P1–P8 [власна]', 'standard':'ISO/IEC 27001:2022 A.8.3', 'severity':'CRITICAL', 'risk':'T2', 'recommendation':'Заборонити міжпроєктний доступ, перевірити RBAC/ABAC та мережеві правила.', 'fn':check_project_isolation},
    'CI-01': {'name':'Захист CI/CD runner [власна]', 'standard':'ISO/IEC 27001:2022 A.8.25', 'severity':'CRITICAL', 'risk':'T3/T4', 'recommendation':'Ізолювати та захистити runner, прибрати довгострокові секрети.', 'fn':check_cicd_secrets},
    'CR-01': {'name':'Мінімальна версія TLS 1.3', 'standard':'ISO/IEC 27001:2022 A.8.24', 'severity':'MEDIUM', 'risk':'T1', 'recommendation':'Встановити мінімальну версію TLS 1.3.', 'fn':check_tls},
    'CR-02': {'name':'AES-256-GCM і KMS', 'standard':'ISO/IEC 27001:2022 A.8.24', 'severity':'HIGH', 'risk':'T2/T4', 'recommendation':'Увімкнути AES-256-GCM та централізований KMS.', 'fn':check_encryption},
    'BC-01': {'name':'Захищені резервні копії', 'standard':'ISO/IEC 27001:2022 A.8.13', 'severity':'HIGH', 'risk':'T2/T3', 'recommendation':'Налаштувати шифрування, immutable backup, інтервал ≤60 хв та DR-тест ≤90 днів.', 'fn':check_backup},
    'LG-01': {'name':'Централізоване журналювання', 'standard':'ISO/IEC 27001:2022 A.8.15', 'severity':'HIGH', 'risk':'T1/T3', 'recommendation':'Додати відсутні джерела подій та зберігати журнали щонайменше 180 днів.', 'fn':check_logging},
}


def load_json(path):
    with path.open('r', encoding='utf-8') as f:
        return json.load(f)


def main():
    p = argparse.ArgumentParser(description='DevBridge Security Compliance Checker')
    p.add_argument('--config', type=Path, default=BASE/'system_config.json')
    p.add_argument('--checklist', type=Path, default=BASE/'control_checklist.json')
    p.add_argument('--output', type=Path, default=BASE/'reports'/'compliance_report.json')
    args = p.parse_args()
    try:
        config = load_json(args.config)
        checklist = load_json(args.checklist)
        ids = checklist['controls']
        if not isinstance(ids, list) or not ids or len(ids) != len(set(ids)):
            raise ValueError('controls має бути непорожнім списком унікальних ID')
        unknown = [id_ for id_ in ids if id_ not in CHECK_REGISTRY]
        if unknown:
            raise ValueError('Невідомі ID: '+', '.join(unknown))
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as e:
        print('[ERROR] Не вдалося завантажити конфігурацію:', e)
        return 2
    results = []
    print('DevBridge Solutions — Security Controls Checker')
    print('='*64)
    for id_ in ids:
        item = CHECK_REGISTRY[id_]
        try:
            passed, details = item['fn'](config)
        except (TypeError, ValueError, AttributeError) as e:
            passed, details = False, 'Некоректні дані конфігурації: ' + str(e)
        result = {'id':id_, 'name':item['name'], 'status':'PASS' if passed else 'FAIL', 'severity':item['severity'], 'standard':item['standard'], 'risk':item['risk'], 'details':details, 'recommendation':None if passed else item['recommendation']}
        results.append(result)
        print(f"[{result['status']}] {id_} | {item['severity']} | {item['name']} | {item['standard']} | ризик: {item['risk']}")
        print('  ' + details)
        if not passed:
            print('  Рекомендація: ' + item['recommendation'])
    passed_count = sum(x['status']=='PASS' for x in results)
    report = {'organization':'DevBridge Solutions', 'generated_at':datetime.now(timezone.utc).isoformat(), 'summary':{'total':len(results), 'pass':passed_count, 'fail':len(results)-passed_count}, 'results':results, 'note':'Перевірено лише модельну JSON-конфігурацію, не фактичну хмарну інфраструктуру.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print('='*64)
    print(f"Підсумок: PASS {passed_count}/{len(results)}, FAIL {len(results)-passed_count}/{len(results)}")
    print('JSON-звіт:', args.output)
    return 0 if passed_count == len(results) else 1

if __name__ == '__main__':
    raise SystemExit(main())
