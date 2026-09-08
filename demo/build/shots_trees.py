# The toolkit's contact sheet, run against group 1's own artconfig.
#
#   blender --background --python shots_trees.py -- <piece-name>
#
# shots.py is the toolkit's file and is imported unmodified. The only thing this
# adds is putting art_trees/ ahead of art/ on sys.path, so `import artconfig`
# inside shots.py resolves to the tree kit's viewing distances rather than the
# fire kit's. See the header of art_trees/artconfig.py for why the two groups
# cannot share one.
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, 'art_trees'))
sys.path.insert(1, os.path.join(HERE, 'art'))

import shots                                        # noqa: E402

shots.main()
