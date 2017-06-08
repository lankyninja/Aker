Given the following hosts and categories in the provided category configuration the possible output would be

* hosts 
- anazmy.secure.some-client.com - name: anazmy host (resolves to 125.87.22.8)
- home.lanky.com - name: lanky host (resolves to 10.10.0.1)
- 125.88.22.3 - name: some host
- ci.private.some-client.com - name: ci host (resolves to 125.88.13.3)
- 11.11.11.35 - name: example-app-01
- localhost - name: local host (resolves to 127.0.0.1 )

* sample tui categories
\+ test
  \- anazmy host (anazmy.secure.some-client.com)
  \- example-app-01 (11.11.11.35)
\+ some-client
  \- anazmy host  (anazmy.secure.some-client.com)
  \- some host  (125.88.22.3)
  \- ci host  (ci.private.some-client.com)
lanky host  (home.lanky.com)
local host  (localhost)
