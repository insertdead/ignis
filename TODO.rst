TODO
====
1. Create a CLI or create some other way to allow usage of this library between languages
2. Complete ``ignis.py`` file and ``Ignis`` class
3. Create a cache system
4. Custom scopes for every subclass?? (increased security)
   - Perhaps use authorization codes instead
5. Check length of credentials to prevent garbage being sent to the server
6. Make lib available exclusively to python3.10 and up to enable alternative syntax for unions (maybe)
7. Use OAuth Authorize functionality to get a token (Or add as an alternative to using dev credentials)
   - Would especially be useful for the Home-assistant integration as not all users will be willing to create dev tokens
8. Restrict access to entities and actions outside of the provided scope (Prevent unneeded fatal exceptions)