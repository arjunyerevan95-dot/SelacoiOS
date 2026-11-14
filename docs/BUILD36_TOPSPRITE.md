# Build36: new-data startup compatibility

Observed installed build35 terminates during WeaponSprite parsing of the updated v0.200 game data. This is not an ongoing load or a pinch-editor failure.

The owned reference engine identifies itself as v0.34-2063-gfd4b0b60d8-m. Its WeaponSprite parser compares TopSprite after Offset2 and, on success, jumps directly to the next-property/closing-brace loop. It consumes no value and stores no flag. Unknown properties retain their error path. The implementation mirrors this narrowly evidenced compatibility-marker behavior, not a guessed rendering feature.

Architecture: texture metadata is parsed before gameplay. Competing hypothesis: graphics failure; observed graphics initialization and explicit fatal parser diagnostic instead support parser mismatch. Distinguishing device evidence is progression beyond this named parser error, or the next explicit diagnostic. A later failure must be handled separately.

Only this parser branch changes. Existing rendering, framegen, editor, stable bundle identity and saves/data are preserved. No retail assets or script bodies included. Tests cover the exact replacement, idempotence and rejection of unexpected source. Phone startup/gameplay testing remains necessary; this is NOT full v0.200 compatibility certification.
