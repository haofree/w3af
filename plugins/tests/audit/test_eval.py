'''
test_eval.py

Copyright 2012 Andres Riancho

This file is part of w3af, w3af.sourceforge.net .

w3af is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation version 2 of the License.

w3af is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with w3af; if not, write to the Free Software
Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
'''

from ..helper import PluginTest, PluginConfig


class TestEval(PluginTest):
    
    target_echo = 'http://moth/w3af/audit/eval/eval.php'
    target_delay = 'http://moth/w3af/audit/eval/eval-blind.php'
    
    _run_configs = {
        'echo': {
            'target': target_echo + '?c=',
            'plugins': {
                 'audit': (PluginConfig('eval',
                                        ('useEcho', True, PluginConfig.BOOL)),
                            ),
                 }
            },

        'delay': {
            'target': target_delay + '?c=',
            'plugins': {
                 'audit': (PluginConfig('eval',
                                        ('useEcho', False, PluginConfig.BOOL)),
                            ),
                 }
            }                    
        }
    
    def test_found_eval_echo(self):
        cfg = self._run_configs['echo']
        self._scan(cfg['target'], cfg['plugins'])
        
        vulns = self.kb.getData('eval', 'eval')
        self.assertEquals(1, len(vulns))
        
        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals('eval() input injection vulnerability', vuln.getName())
        self.assertEquals("c", vuln.getVar())
        self.assertEquals(self.target_echo, str(vuln.getURL() ))
    
    def test_found_eval_delay(self):
        cfg = self._run_configs['delay']
        self._scan(cfg['target'], cfg['plugins'])
        
        vulns = self.kb.getData('eval', 'eval')
        self.assertEquals(1, len(vulns))
        
        # Now some tests around specific details of the found vuln
        vuln = vulns[0]
        self.assertEquals('eval() input injection vulnerability', vuln.getName())
        self.assertEquals("c", vuln.getVar())
        self.assertEquals(self.target_delay, str(vuln.getURL() ))
        