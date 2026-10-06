p = "android/app/src/main/AndroidManifest.xml"
s = open(p, encoding="utf-8").read()
if "WaService" not in s:
    queries = ('<queries><package android:name="com.whatsapp"/>'
               '<package android:name="com.whatsapp.w4b"/></queries>\n    ')
    s = s.replace("<application", queries + "<application", 1)
    svc = ('<service android:name="com.example.wabulk.WaService" android:exported="false" '
           'android:label="@string/app_name" '
           'android:permission="android.permission.BIND_ACCESSIBILITY_SERVICE">'
           '<intent-filter><action android:name="android.accessibilityservice.AccessibilityService"/></intent-filter>'
           '<meta-data android:name="android.accessibilityservice" android:resource="@xml/accessibility_config"/>'
           '</service>\n    </application>')
    s = s.replace("</application>", svc, 1)
    open(p, "w", encoding="utf-8").write(s)
print("manifest patched")
