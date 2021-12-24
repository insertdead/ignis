Todo list
====
#. Create a CLI or create some other way to allow usage of this library between languages

   - For another project


#. Create a cache system

   - The current implementation seems a bit useless, as msgpack is best used for IPC and RPC, but that's not my intent.
      Perhaps I could use the redis db because of its fast nature and it being designed for such things.

   - This would best be done in another branch, with its own pr, because of its scale.

#. Custom scopes for every subclass?? (increased security)
   
   - Perhaps use authorization codes instead

#. Check length of credentials to prevent garbage being sent to the server

#. Make lib available exclusively to python3.10 and up to enable alternative syntax for unions (maybe)

#. Use OAuth Authorize functionality to get a token (Or add as an alternative to using dev credentials)
   
   - Would especially be useful for the Home-assistant integration as not all users will be willing to create dev tokens

#. Restrict access to entities and actions outside of the provided scope (Prevent unneeded fatal exceptions)

#. Add ID, token and code types (classes) for more robust error handling
   
   - Note that this might not be all that useful for the scope of this project, though it may be fun to implement nevertheless :)
   - This might be more useful to add to another general-purpose library, instead of hard-coded into this one, focused more on OAuth (2.0)
