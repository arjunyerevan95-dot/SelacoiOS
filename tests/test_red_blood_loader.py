"""Source-contract tests on the actual generated Objective-C++ launch code.
These do not replace Apple SDK compilation or an on-device mod test.
"""
from pathlib import Path
import sys, unittest
root=Path(sys.argv.pop(1))
source=(root/'src/common/platform/ios/i_platform_runtime.mm').read_text()
class RedBloodLoaderContracts(unittest.TestCase):
 def test_other_autoload_stays_disabled(self):
  self.assertIn('"-noautoload"',source)
  self.assertIn('"-noautoexec"',source)
 def test_single_exact_archive(self):
  self.assertEqual(source.count('@"Mods/Brutal Selaco.pk3"'),1)
  self.assertEqual(source.count('arguments.emplace_back("-file")'),1)
 def test_exact_verified_digest(self):
  self.assertIn('@"c8889ddb25ea89601f19275c02b89fe4d3004220e40fdb1779a1e5a404427cac"] &&\n            HasZipSignature(redBlood)',source)
 def test_absent_or_directory_skips_hash(self):
  self.assertIn('redBloodExists && !redBloodIsDirectory\n            ? SHA256ForFile(redBlood) : nil;',source)
 def test_no_directory_enumeration_or_extra_actions(self):
  block=source[source.index('// Optional, exact allowlisted'):source.index('std::vector<char *> argv;')]
  self.assertNotIn('contentsOfDirectory',block)
  self.assertNotIn('for (',block)
  self.assertEqual(block.count('arguments.emplace_back('),2)
 def test_selection_precedes_argv_and_has_both_outcomes(self):
  self.assertLess(source.index('red_blood_mod_selected'),source.index('std::vector<char *> argv;'))
  self.assertIn('red_blood_mod_not_selected',source)
if __name__=='__main__': unittest.main()
