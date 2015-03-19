# Introduction #


This is a list of milestones for Flax 1.0, vaguely described. Things may well change.


# Details #


  * [D1](D1.md) - Prototype web front end
    * HTMLTemplate files for the main Flax web pages.
    * CSS for layout/styling of the HTML.
    * Python to render the templates as HTML for viewing in a browser.


  * [D2](D2.md) - Web server
    * Python code for serving the web pages from D1.
    * The code will contain stubs for functionality to be implemented as part of later milestones.


  * D3 - Filter system design
    * A document describing the interface for document filters: [FilterInterface](FilterInterface.md).
    * A document describing how Flax will run document filters: [Indexer](Indexer.md).




  * D4 - Filter System Implementation
    * Python code implementing the designs from D3.


  * D5 - Document filters:  [FilteringImplementation](FilteringImplementation.md)
    * Plain text.
    * HTML.
    * MS Word.
    * MS Excel.
    * MS Power Point.
    * PDF.


  * [D6](D6.md) - Document Collection Design.
    * Constituent documents specification (i.e. how we select documents of the collection - paths, formats, exclusions, date (and age) ranges).
    * Indexing.
    * Scheduling of indexing.


  * D7 - Document Collection Implementation.
    * Python code implementing the design from D6.


  * D8 - Query building
    * Python code to process input from simple and advanced search web pages.


  * D9 - Search Results
    * Python code to process the search results return by Xapian


  * D10 - Global options
    * Python code for dealing with things like the admin password, how results are presented, etc.


  * D11 - Persistence.
    * Python code to ensure that data persists.


  * D12 - Installer
    * A Windows installer for the whole Flax system.


  * D13 - Documentation
    * Administrator documentation
    * End user "How to do searches" documentation.


  * D14 - Complete system
    * Flax system 1.0 completion