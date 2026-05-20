`scl`: make syslogconf awk converter installation optional

Add build options for both CMake and autotools to optionally omit
installation of `scl/syslogconf/convert-syslogconf.awk`.

The converter remains installed by default, preserving existing
behavior for current users.
