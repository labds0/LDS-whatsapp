#!/usr/bin/env bash
# يُنسخ الكود الأصلي (Java) داخل مشروع أندرويد الذي ينشئه Capacitor
set -e
PKG_DIR=android/app/src/main/java/com/example/wabulk
mkdir -p "$PKG_DIR" android/app/src/main/res/xml android/app/src/main/res/values
cp android-plugin/java/*.java "$PKG_DIR/"
cp android-plugin/res/xml/*.xml android/app/src/main/res/xml/
cp android-plugin/res/values/wabulk_strings.xml android/app/src/main/res/values/
python3 android-plugin/patch_manifest.py
