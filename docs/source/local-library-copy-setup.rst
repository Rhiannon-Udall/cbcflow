Setting Up A Library From a Remote
==================================

Creating a working ``cbcflow`` library is *slightly* more complicated than just cloning a remote library.
First, though, you should indeed clone it!

Once that's done, there's one more thing to do!
``cbcflow`` requires custom a custom driver for ``git merge`` to handle json files (see :doc:`cbcflow-git-merging` for details).
This can be offloaded entirely, as long as we configure our library correctly, but this must be done locally since the relevant configuration cannot be globally tracked.
This also means that valid merging can *only* be done locally - you can't just hit merge in gitlab and expect it all to work!
In real usage this should be handled by a team of experts (reach out if you want to join that team!), but for local usage we do want to make sure things get setup right.
The library you have cloned, assuming it is setup correctly according to :doc:`library-setup-from-scratch`, will have the files ``.gitattributes``, ``.gitconfig``, and ``setup-cbcflow-merge-strategy.sh``.
Assuming this is the case, just run the bash script, and everything should be set!
If those files aren't present, it's very easy to make them yourself, just follow the instructions on :doc:`library-setup-from-scratch`.