# Todo list
1. Create a CLI or create some other way to allow usage of this library between languages
   - For another project


2. Use OAuth Authorize functionality to get a token (Or add as an alternative to using dev credentials)
   - Would especially be useful for the Home-assistant integration as not all users will be willing to create dev tokens

3. Add ID, token and code types (classes) for more robust error handling
   - Note that this might not be all that useful for the scope of this project, though it may be fun to implement nevertheless :)
   - This might be more useful to add to another general-purpose library, instead of hard-coded into this one, focused more on OAuth (2.0)

4. Related to #3 - Create a class that builds a scope from arguments, for better testing capabilities.

5. Refresh token when scope is changed

6. Method in AbstractConfig/AbstractClient to create an entity, and delete it?