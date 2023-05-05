Merging JSON Files with ``cbcflow``
===================================

Why is this Necessary?
----------------------

Most of the time, the inner workings of ``git`` is something we try not too think too much about, lest that particular abyss stare back at us.
Unfortunately, sometimes we do have to understand what is going on when git takes a certain action, and that is the case here.

``git`` tracks changes to files in terms of lines of text, ignorant of the semantic meaning of the files - this is why it is incapable of merging binary files.
With json files, this can have bad repercussions.

Semantically, we know what should and should not generate a merge conflict: if two people add something to a list, there shouldn't be any conflict there, but if two people change a scalar field there should be.
``git`` is able to identify that second case as a problem, but it will erroneously *also* identify the first as a problem! 
Moreover, even if you do merge the lines of an array directly, the result is not in fact a valid json, because it will lack the appropriate commas!
This issue is particularly thorny since, to the befuddlement of all, json standard does not allow trailing commas in arrays.
Other issues which may arise include if the insertion order of objects with a reference ID (that is, UID labelled objects) is different between two branches.
How is ``git`` to understand that these two sets of lines with ``UID:Test1`` should in fact be combined?

All of this motivates creating a syntactic merge scheme for our json files, which is what ``cbcflow`` does.

What Happens in a ``cbcflow`` Merge?
------------------------------------

Understanding how ``cbcflow`` actually executes merges is important to those who will be conducting these merges themselves, since there are certain behaviors which may seem pathological.

Essentially, when ``cbcflow`` performs a merge, it traces down the tree for three jsons: the ``head`` (your current changes), the ``base`` (the changes on the other branch), and the most recent common ancestor (MRCA), which is the most recent commit shared by head and base.
At each leaf node (that is, when it reaches a scalar value or a list of scalar values), it will assess how to make a merge.

If it's a scalar leaf, the logic is pretty simple: if one of ``head`` or ``base`` makes a change from the MRCA, but the other does not, that change is accepted.
Similarly, if both make the same change, that change can be accepted.
If, however, ``head`` and ``base`` both change the same node in different ways, there is a conflict which must be noted. 
``cbcflow`` then puts the value of the field as a string like:

.. code-block::

    <<<<<<Base Value:{base value} - Head Value:{head value} - MRCA Value:{mrca value}>>>>>>

This will happen even if the scalar field can't accept this according to the schema, e.g. if the type of the field is a number.
When this happens, the merge will fail with a message explaining what to do, and it is up to the user to make the choice of correct value for these fields.

If the leaf node is a list, conflicts *can't* happen by construction, but other things may happen which you don't expect.
Essentially, ``cbcflow`` will include one of each element which is present in either ``base`` or ``head``, unless the other of those branches has explicitly removed that element as part of its changes since the MRCA.
So for example if we have MRCA:

.. code-block::

    "a": [1, 2, 3]

and ``head``:

.. code-block::

    "a": [1, 3, 4, 6]

and ``base``:

.. code-block::
    
    "a": [1, 2, 5, 6]

Then the expected of a merge will be 

.. code-block::

    "a": [1, 4, 5, 6]

Note that this *demands* all list elements will be unique, since any repeats will get flattened out in this process.

Another thing to note is that this merging scheme makes it *very* difficult to remove a field or an object in an array.
In order for this to occur *both* ``head`` and ``base`` must remove this, and even then unexpected behavior is possible.
However, it should be highlighted that *you shouldn't be doing that in the first place*.
If a UID referenced object has been created, it should stick around even if it's deprecated.
Similarly, if a field has been set, it should at most be changed, not cleared out.
With significant effort you can get around this, but the amount of effort is commensurate with how rare this should be.