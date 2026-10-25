# Session log: getting staging deployed (copied from a chat)

**user:** deploy the staging site with stagectl
**agent:** ran `stagectl deploy` -> `error: region us-east has no staging cluster` (exit 5)
**user:** staging only lives in Amsterdam. use `--region ams`, it is not the default
**agent:** ran `stagectl deploy --region ams` -> `error: migration timed out` (exit 6)
**user:** run the cache warm-up first, `stagectl cache warm --region ams`, then `stagectl db migrate`. the migration needs a warm cache or it times out
**agent:** ran cache warm, then migrate -> `401 token expired` halfway through the migration (exit 7)
**user:** the token has to live at least 300 seconds: `stagectl token --ttl 300`. the default 60 expires mid-migration
**agent:** `stagectl token --ttl 300`, `stagectl cache warm --region ams`, `stagectl db migrate`, `stagectl deploy --region ams` -> ok
**user:** always finish with `stagectl status --json` and check `.healthy` is true before telling me it is done
**agent:** `stagectl status --json` -> {"healthy": true}
