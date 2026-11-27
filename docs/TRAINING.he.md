# מדריך הפעלה — IvritLM (עברית)

המדריך הזה מוביל אותך מהתקנה ראשונית ועד הפעלת אימון ושמירת המודל ב-Google Drive. צריך לבצע את חיבור Drive פעם אחת בלבד.

## 1. מה צריך להכין?

- מחשב Windows עם Python 3.11 ומעלה.
- חשבון GitHub עם גישה למאגר IvritLM.
- חשבון Google שבו יישמרו קובצי המודל.
- קובץ טקסט UTF-8 שיש לך הרשאה מפורשת להשתמש בו לאימון.

## 2. חיבור Google Drive — פעם אחת

### א. הורדת קובץ OAuth הנכון

1. היכנס אל [Google Cloud Console](https://console.cloud.google.com/).
2. צור פרויקט או בחר פרויקט קיים.
3. פתח APIs & Services → Library והפעל **Google Drive API**.
4. הגדר OAuth consent screen. אם האפליקציה במצב Testing, הוסף את חשבון Google שלך כ-Test user.
5. פתח APIs & Services → Credentials.
6. לחץ Create Credentials → OAuth client ID.
7. בחר **Desktop app** והורד את קובץ ה-JSON.

**חשוב:** יש לבחור את קובץ ה-OAuth שהורדת, שבדרך כלל שמו מתחיל ב-`client_secret_`. אין לבחור `token.json`, קובץ Access Token או קובץ JSON אחר. אם מתקבלת השגיאה `Client secrets must be for a web or installed app`, נבחר קובץ לא מתאים.

### ב. הפעלת אשף החיבור

פתח PowerShell בתיקיית המאגר והריץ:

```powershell
python -m pip install -r requirements-model.txt
python scripts/google_drive_auth.py
```

ייפתח חלון בחירת קובץ. בחר את קובץ ה-OAuth מסוג Desktop app שהורדת. לאחר מכן ייפתח דפדפן לאישור הגישה לחשבון Google.

אפשר גם לציין את הנתיב במפורש:

```powershell
python scripts/google_drive_auth.py --client-secrets "C:\נתיב\client_secret.json"
```

בסיום תקבל הודעה על הצלחה וארבעה ערכים. השאר את חלון PowerShell פתוח עד שתעתיק אותם ל-GitHub.

### ג. שמירת ארבעת הערכים ב-GitHub

1. פתח [GitHub Actions Secrets](https://github.com/avtsye/IvritLM/settings/secrets/actions).
2. לחץ **New repository secret**.
3. צור את ארבעת הסודות הבאים, אחד בכל פעם:

| שם הסוד | מה להדביק |
|---|---|
| `DRIVE_CLIENT_ID` | הערך שמופיע אחרי אותו שם בסקריפט |
| `DRIVE_CLIENT_SECRET` | הערך שמופיע אחרי אותו שם |
| `DRIVE_REFRESH_TOKEN` | הערך שמופיע אחרי אותו שם |
| `DRIVE_FOLDER_ID` | מזהה תיקיית IvritLM Models |

אין להוסיף מרכאות. אין לשלוח את הערכים לאדם אחר, לצ'אט, ל-Issue או לקובץ במאגר. אם אחד מהם נחשף, יש לבטל את ההרשאה ב-Google וליצור חיבור חדש.

### ד. בדיקת החיבור

לאחר שמירת ארבעת הסודות, הפעל אימון בדיקה קטן דרך GitHub Actions. אם שלב Restore checkpoint או Upload checkpoint מצליח, החיבור ל-Drive תקין.

ב-Google Drive תיווצר תיקייה בשם **IvritLM Models**. בתוכה תיווצר תיקייה לכל גרסת מודול, למשל `0.1.0`. הקבצים יישמרו בתיקיית הגרסה, ו-`latest.json` בתיקייה הראשית יצביע על הקבצים העדכניים.

> אם אפליקציית OAuth מוגדרת External ובמצב Testing, Google עשויה לפוג את Refresh Token לאחר שבעה ימים. לשימוש מתמשך יש להעביר את מסך ההסכמה ל-In production ולפעול לפי דרישות Google.

## 3. יצירת GitHub Token לדף הניהול

1. פתח [יצירת Fine-grained token](https://github.com/settings/personal-access-tokens/new).
2. בחר גישה למאגר IvritLM בלבד.
3. תחת Repository permissions הגדר **Actions: Read and write** וגם **Metadata: Read-only**.
4. צור את האסימון והעתק אותו. GitHub מציג אותו פעם אחת בלבד.

בדף הניהול הדבק את האסימון בשדה GitHub token. הוא נשמר בזיכרון הלשונית בלבד. לחץ "ניקוי אסימון" או סגור את הלשונית כדי למחוק אותו מהדף.

## 4. הפעלת אימון

1. ודא שקובץ הקורפוס כבר נמצא במאגר ושהוא UTF-8 עם סיומת `.txt`.
2. בדוק שיש לך הרשאה להשתמש בכל הטקסט לאימון. קובץ במאגר ציבורי יהיה גלוי לציבור.
3. בדף הניהול, בשדה נתיב קורפוס, כתוב למשל `data/corpus/train.txt`.
4. בחר מספר צעדי אימון נוספים ו-Batch size. לבדיקת התחלה מומלץ להשאיר את ברירות המחדל.
5. לחץ **הפעלת אימון והפקת GGUF**.
6. פתח את רשימת הריצות כדי לעקוב אחרי התהליך.

האימון ממשיך מה-Checkpoint האחרון ב-Drive. אם זו הפעם הראשונה, המודל מתחיל ממשקולות אקראיות. ריצת CPU קטנה בודקת שהתהליך עובד; היא אינה מאמנת מודל שימושי.

## 6. בדיקת תוצאות

- ב-GitHub Actions בדוק שכל השלבים הסתיימו בהצלחה.
- ב-Google Drive פתח `IvritLM Models/<module-version>/`.
- קובץ `.pt` הוא Checkpoint להמשך אימון.
- קובץ `.gguf` הוא ייצוא לשימוש בכלי הסקה תומכים.
- `metrics-*.json` מכיל מדדי אימון.
- `latest.json` נמצא בתיקייה הראשית ומפנה לקובץ האחרון.

## 7. פתרון תקלות נפוצות

| הודעה או בעיה | מה לעשות |
|---|---|
| `Client secrets must be for a web or installed app` | נבחר `token.json`. יש לבחור OAuth Client JSON מסוג Desktop app. |
| `Google did not return a Refresh Token` | הרץ שוב את האשף ואשר גישה מחדש. |
| `Missing Google Drive OAuth secrets` | בדוק שכל ארבעת GitHub Secrets קיימים ושמותיהם מדויקים. |
| `DRIVE_FOLDER_ID` חסר | הוסף את מזהה התיקייה שהאשף הדפיס. |
| ריצת אימון נכשלת על נתיב קורפוס | בדוק שהקובץ קיים ב-main, שהנתיב יחסי ושהסיומת היא TXT. |
| אין GGUF | פתח את יומן הריצה; ייתכן ששלב ההמרה נכשל. Checkpoint נשמר קודם לכן. |

## מה עדיין לא אוטומטי?

טופס בדיקת המקור בודק מקור ומפיק דוח. הוא עדיין אינו מוריד את כל התוכן ואינו מכניס אותו אוטומטית לקורפוס. עד להשלמת קליטת מקורות, יש להכין קובץ TXT מאושר ולהעלות אותו למאגר. אין להשתמש בתוכן שאין לך הרשאה מפורשת לאמן עליו.

## קישורים

- [דף הניהול](https://raw.githack.com/avtsye/IvritLM/main/site/index.html)
- [המאגר](https://github.com/avtsye/IvritLM)
- [GitHub Actions](https://github.com/avtsye/IvritLM/actions)
- [מדריך באנגלית](TRAINING.md)
