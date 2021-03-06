'''
sqli.py

Copyright 2006 Andres Riancho

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

from core.controllers.basePlugin.baseAuditPlugin import baseAuditPlugin
from core.data.fuzzer.fuzzer import createMutants
from core.data.options.optionList import optionList
from core.data.esmre.multi_re import multi_re

import core.controllers.outputManager as om
import core.data.constants.dbms as dbms
import core.data.constants.severity as severity
import core.data.kb.knowledgeBase as kb
import core.data.kb.vuln as vuln


class sqli(baseAuditPlugin):
    '''
    Find SQL injection bugs.
    @author: Andres Riancho ( andres.riancho@gmail.com )
    '''
    
    SQL_ERRORS = (
        # ASP / MSSQL
        (r'System\.Data\.OleDb\.OleDbException', dbms.MSSQL),
        (r'\[SQL Server\]', dbms.MSSQL),
        (r'\[Microsoft\]\[ODBC SQL Server Driver\]', dbms.MSSQL),
        (r'\[SQLServer JDBC Driver\]', dbms.MSSQL),
        (r'\[SqlException', dbms.MSSQL),
        (r'System.Data.SqlClient.SqlException', dbms.MSSQL),
        (r'Unclosed quotation mark after the character string', dbms.MSSQL),
        (r"'80040e14'", dbms.MSSQL),
        (r'mssql_query\(\)', dbms.MSSQL),
        (r'odbc_exec\(\)', dbms.MSSQL),
        (r'Microsoft OLE DB Provider for ODBC Drivers', dbms.MSSQL),
        (r'Microsoft OLE DB Provider for SQL Server', dbms.MSSQL),
        (r'Incorrect syntax near', dbms.MSSQL),
        (r'Sintaxis incorrecta cerca de', dbms.MSSQL),
        (r'Syntax error in string in query expression', dbms.MSSQL),
        (r'ADODB\.Field \(0x800A0BCD\)<br>', dbms.MSSQL),
        (r"Procedure '[^']+' requires parameter '[^']+'", dbms.MSSQL),
        (r"ADODB\.Recordset'", dbms.MSSQL),
        (r"Unclosed quotation mark before the character string", dbms.MSSQL),
        (r"'80040e07'", dbms.MSSQL),
        (r'Microsoft SQL Native Client error', dbms.MSSQL),
        # DB2
        (r'SQLCODE', dbms.DB2),
        (r'DB2 SQL error:', dbms.DB2),
        (r'SQLSTATE', dbms.DB2),
        (r'\[CLI Driver\]', dbms.DB2),
        (r'\[DB2/6000\]', dbms.DB2),
        # Sybase
        (r"Sybase message:", dbms.SYBASE),
        (r"Sybase Driver", dbms.SYBASE),
        (r"\[SYBASE\]", dbms.SYBASE),
        # Access
        (r'Syntax error in query expression', dbms.ACCESS),
        (r'Data type mismatch in criteria expression.', dbms.ACCESS),
        (r'Microsoft JET Database Engine', dbms.ACCESS),
        (r'\[Microsoft\]\[ODBC Microsoft Access Driver\]', dbms.ACCESS),
        # ORACLE
        (r'(PLS|ORA)-[0-9][0-9][0-9][0-9]', dbms.ORACLE),
        # POSTGRE
        (r'PostgreSQL query failed:', dbms.POSTGRE),
        (r'supplied argument is not a valid PostgreSQL result', dbms.POSTGRE),
        (r'pg_query\(\) \[:', dbms.POSTGRE),
        (r'pg_exec\(\) \[:', dbms.POSTGRE),
        # MYSQL
        (r'supplied argument is not a valid MySQL', dbms.MYSQL),
        (r'Column count doesn\'t match value count at row', dbms.MYSQL),
        (r'mysql_fetch_array\(\)', dbms.MYSQL),
        (r'mysql_', dbms.MYSQL),
        (r'on MySQL result index', dbms.MYSQL),
        (r'You have an error in your SQL syntax;', dbms.MYSQL),
        (r'You have an error in your SQL syntax near', dbms.MYSQL),
        (r'MySQL server version for the right syntax to use', dbms.MYSQL),
        (r'\[MySQL\]\[ODBC', dbms.MYSQL),
        (r"Column count doesn't match", dbms.MYSQL),
        (r"the used select statements have different number of columns",
            dbms.MYSQL),
        (r"Table '[^']+' doesn't exist", dbms.MYSQL),
        (r"DBD::mysql::st execute failed", dbms.MYSQL),
        (r"DBD::mysql::db do failed:", dbms.MYSQL),
        # Informix
        (r'com\.informix\.jdbc', dbms.INFORMIX),
        (r'Dynamic Page Generation Error:', dbms.INFORMIX),
        (r'An illegal character has been found in the statement',
            dbms.INFORMIX),
        (r'\[Informix\]', dbms.INFORMIX),
        (r'<b>Warning</b>:  ibase_', dbms.INTERBASE),
        (r'Dynamic SQL Error', dbms.INTERBASE),
        # DML
        (r'\[DM_QUERY_E_SYNTAX\]', dbms.DMLDATABASE),
        (r'has occurred in the vicinity of:', dbms.DMLDATABASE),
        (r'A Parser Error \(syntax error\)', dbms.DMLDATABASE),
        # Java
        (r'java\.sql\.SQLException', dbms.JAVA),
        (r'Unexpected end of command in statement', dbms.JAVA),
        # Coldfusion
        (r'\[Macromedia\]\[SQLServer JDBC Driver\]', dbms.MSSQL),
        # Generic errors..
        (r'SELECT .*? FROM .*?', dbms.UNKNOWN),
        (r'UPDATE .*? SET .*?', dbms.UNKNOWN),
        (r'INSERT INTO .*?', dbms.UNKNOWN),
        (r'Unknown column', dbms.UNKNOWN),
        (r'where clause', dbms.UNKNOWN),
        (r'SqlServer', dbms.UNKNOWN)
    )
    _multi_re = multi_re( SQL_ERRORS )
    
    SQLI_STRINGS = (u"d'z\"0",)

    def __init__(self):
        baseAuditPlugin.__init__(self)
        
        # Internal variables
        self._errors = []

    def audit(self, freq):
        '''
        Tests an URL for SQL injection vulnerabilities.
        
        @param freq: A fuzzableRequest
        '''
        om.out.debug('SQLi plugin is testing: ' + freq.getURL())

        oResponse = self._uri_opener.send_mutant(freq)
        mutants = createMutants(freq, self.SQLI_STRINGS, oResponse=oResponse)

        for mutant in mutants:
            # Only spawn a thread if the mutant has a modified variable
            # that has no reported bugs in the kb
            if self._has_no_bug(mutant):
                args = (mutant,)
                kwds = {'callback': self._analyze_result }
                self._run_async(meth=self._uri_opener.send_mutant, args=args,
                                                                    kwds=kwds)
        self._join()
            
    def _analyze_result(self, mutant, response):
        '''
        Analyze results of the _send_mutant method.
        '''
        with self._plugin_lock:
            if self._has_no_bug(mutant):

                sql_error_list = self._findsql_error(response)
                orig_resp_body = mutant.getOriginalResponseBody()
                
                for sql_regex, sql_error_string, dbms_type in sql_error_list:
                    if not sql_regex.search(orig_resp_body):
                        # Create the vuln,
                        v = vuln.vuln(mutant)
                        v.setPluginName(self.getName())
                        v.setId(response.id)
                        v.setName('SQL injection vulnerability')
                        v.setSeverity(severity.HIGH)
                        v.addToHighlight(sql_error_string)
                        v['error'] = sql_error_string
                        v['db'] = dbms_type
                        v.setDesc('SQL injection in a %s was found at: %s' %
                                  (v['db'], mutant.foundAt()))
                        kb.kb.append(self, 'sqli', v)
                        break
    
    def end(self):
        '''
        This method is called when the plugin wont be used anymore.
        '''
        self._join()
        self.printUniq(kb.kb.getData('sqli', 'sqli'), 'VAR')
    
    def _findsql_error(self, response):
        '''
        This method searches for SQL errors in html's.
        
        @parameter response: The HTTP response object
        @return: A list of errors found on the page
        '''
        res = []
        
        for match, regex_str, regex_comp, dbms_type in self._multi_re.query( response.body ):
            msg = (u'A SQL error was found in the response supplied by '
               'the web application, the error is (only a fragment is '
               'shown): "%s". The error was found on response with id %s.'
               % (match.group(0), response.id))
            om.out.information(msg)
            res.append((regex_comp, match.group(0), dbms_type))
        return res
        
    def getOptions(self):
        '''
        @return: A list of option objects for this plugin.
        '''    
        ol = optionList()
        return ol

    def setOptions(self, OptionList):
        '''
        This method sets all the options that are configured using the user interface 
        generated by the framework using the result of getOptions().
        
        @parameter OptionList: A dictionary with the options for the plugin.
        @return: No value is returned.
        ''' 
        pass

    def getPluginDeps(self):
        '''
        @return: A list with the names of the plugins that should be run before the
        current one.
        '''
        return []
    
    def getLongDesc(self):
        '''
        @return: A DETAILED description of the plugin functions and features.
        '''
        return '''
        This plugin finds SQL injections. To find this vulnerabilities the plugin
        sends the string d'z"0 to every injection point, and searches for SQL errors
        in the response body.
        '''
