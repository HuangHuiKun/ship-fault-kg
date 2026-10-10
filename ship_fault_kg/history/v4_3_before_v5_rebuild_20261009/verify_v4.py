"""Compatibility entry point; V4.2 tests are preserved in the revision backup."""
import unittest
from verify_revision import RevisionTests

if __name__=='__main__':
    unittest.main(verbosity=2)
