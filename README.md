# RenameAPK
Current work-in-progress

Final goal: Given a library of smali files from an APK which have been manually renamed after analysis, it takes the same library from a different APK which was decompiled with proguard (and thus has different naming) and by comparing the two libraries it will re-name the new smali library files to match the known naming of the original library files.
