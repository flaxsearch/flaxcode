## General ##

**How much does Flax Basic cost?**

Flax Basic is entirely free to download and use on as many computers as you want.

**What is the minimum specification for Flax Basic?**

You will need a PC running Windows 2000, 2000 Server, 2003 Server, XP or Vista with at least 1GB of RAM (more is recommended) and enough hard disk space to build the databases (these are generally about the same size as the source files you want to be able to search).

**What browsers does Flax Basic support?**

Flax Basic supports Microsoft Internet Explorer version 6 and above and Mozilla Firefox version 1.5 and above.

**How many files can I search?**

Given sufficient memory and hard disk space, Flax Basic can build indexes of millions (and even hundreds of millions) of files.

**What file formats can Flax Basic read?**

Flax Basic currently reads Microsoft Word, Microsoft Excel, Microsoft Powerpoint, plain text, Rich Text Format (RTF), HTML and Adobe Acrobat (PDF) documents. Flax Basic uses the Microsoft IFilter system which is installed with all modern versions of Windows. Note that on some systems the RTF IFilter may not be present (see below) and on most systems the PDF IFilter will not be present unless Acrobat Reader is installed (see below).

**How would I use Flax Basic in my organisation?**

You can use Flax Basic to provide a search facility for individuals (installed on their computer and searching the documents on their computer) or across the whole organisation (installed on a server and searching shared or publically available documents), or a combination of the two.

**Can I modify or extend Flax Basic?**

Flax Basic is open-source licensed under the GPL; this means that you can also download the source code to Flax Basic (see http://www.flax.co.uk for details) and modify it to your requirements. However if you distribute this modified code you must also distribute the source code. If your modifications will be of benefit to other users, you can submit them to the Flax project and they may be incorporated into the next release of the software.

**I would like a feature that is not available in Flax Basic**

The technology that Flax Basic uses (the [Xapian](http://www.xapian.org) search engine library and the [Xappy](http://www.xappy.org) interface library) allow a huge range of search engine functions, far more than are currently available in Flax Basic. [Contact us](http://www.flax.co.uk) and we can discuss how we might help you.

## Other search systems ##

**Why is Flax Basic different to Google Desktop?**

Flax Basic can be run across a network, so you can use it to search files that are shared between computers. Flax Basic also uses a web page interface, so you can easily access it from other computers. Google Desktop is designed to search files on a single computer only, whereas Flax Basic can be used from many computers. The source code for Flax is also freely available.

**Why is Flax Basic different to most other search systems?**

Flax Basic and the entire Flax project are entirely free to download, use and modify (under the terms of the [GPL](http://en.wikipedia.org/wiki/GPL)). There are no restrictions on the number of computers on which you can install the software, the number of documents you can index or the number of users.

## More about Flax Basic ##

**What is Flax Basic based on?**

Flax Basic is based on the Flax search solution platform developed by Lemur Consulting Ltd., an entirely open-source enterprise search system. Flax uses the [Xapian](http://www.xapian.org) search engine library, the [CherryPy](http://www.cherrypy.org) web application server and the [Python](http://www.python.org) programming language to provide a robust, scalable and high-performance search system.

## Getting Started ##

**How do I upgrade to a new version of Flax Basic without losing my data?**

Uninstall Flax Basic (there is an option in the Programs menu) and follow the instructions about upgrading, then install a new version of Flax Basic. The old data will be preserved.

**I didn't choose to install Flax as a Windows Service. How do I start it running?**

If you want to run Flax in the background as a Windows Service, then run the file `C:\Program Files\Flax Basic\startflaxservice.bat` , or start Flax in a command line window by selecting _Start_, _Programs_, _Flax Basic_, Flax Basic (Manual Start) . Remember that once you close this command line window, Flax will stop running.

**How do I back up the Flax Basic databases?**

Flax Basic databases are held in a special 'data' folder (you will have chosen this when you installed Flax Basic). You can back this up by simply copying the appropriate folders. You should only do this when indexing has completed, otherwise you may make a copy of a database that does not contain all the files you might expect.

**How do I change the port that Flax Basic uses?**

Flax Basic is by default available at port 8090; you can change this as follows: First, make sure Flax Basic is not running. If you installed Flax Basic as a Service, you can stop it by running the file `C:\Program Files\Flax Basic\stopflaxservice.bat`, if it is running in a command window then close that window. Then edit the file `C:\Program Files\Flax Basic\conf\cp.conf` using Windows Notepad - change the `server.socket_port = 8090` line to a different port, and save the file. Restart the Flax Basic service if necessary by running the file `C:\Program Files\Flax Basic\startflaxservice.bat` and Flax should now be available on the new port.

**How do I use Flax with Microsoft Internet Information Server (IIS)?**

If you have an existing website (for example `www.mydomain.com`) run on IIS and want to use Flax Basic on the same computer, you can use the following method to set up a Reverse Proxy; this will mean that visitors to your website will see the Flax search pages at `www.mydomain.com/search`

We have successfully used Isapi Rewrite from http://www.helicontech.com - this is not free software, but the cost for a license is very low (£70). You will then need to edit the httpd.conf file that controls all the functions of Isapi Rewrite and add the following lines:
```
RewriteEngine on
RewriteBase /
RewriteRule (.+) http://a.b.c.d:8090/$1 [NC,P]  
```
where a.b.c.d. is the IP address of the server running Flax. Note that there are many, many different ways of setting up this kind of proxy, refer to the Isapi Rewrite documentation and forums for more information.

**How do I customise the search page(s)?**

If you want to change the appearance of any pages you will need to edit the templates in `C:\Program Files\Flax Basic\templates` and the stylesheet in `C:\Program Files\Flax Basic\static\css` (assuming you installed Flax Basic to the default folder). Make a backup of the pages first so you can roll back if you make a mistake! The easiest way to change the appearance of Flax Basic is to edit the `user_banner.html` page, as this is shown at the top of all pages that users see.

**I can't set a password during installation**

Did you try entering a password? The password isn't actually shown as you type it. Try un-installing Flax and re-installing; when you are asked for a password type it in, press Enter, then repeat the process.

**I've forgotten the password I set during installation, how do I reset it?**

First, make sure Flax Basic is not running. If you installed Flax Basic as a Service, you can stop it by running the file `C:\Program Files\Flax Basic\stopflaxservice.bat`, if it is running in a command window then close that window. Then open a command window (_Start_, _Run_, `cmd`) and type:

`cd "C:\Program files\Flax Basic"`
`startflax --set-admin-password`

Enter a new password and close the window, then restart the Flax Basic service if necessary by running the file `C:\Program Files\Flax Basic\startflaxservice.bat` . Remember the password won't be displayed as you type it.

## Indexing ##

**I've created a collection but no documents are being indexed, why?**

First, if you are using scheduled indexing, try a manual index by pressing the 'Start' button. If no files are found you may have either set the wrong Path or there are no files of the type(s) you selected in the Path.

**I'm using scheduled indexing but no documents are being indexed, although the collection is shown as 'Due'**

Remember that when using scheduled indexing, any of the time settings that _do not_ contain a number will need a asterisk - otherwise no indexing will happen. For example, to perform an index at 3am every Wednesday, set the fields as follows:
```
Minutes: *
Hours: 3
Weekdays: 2
Monthdays: *
Months: *
```

**Why can't I index documents in a Windows shared folder?**

Make sure you specify the shared folder correctly in the Path box of the Collection, as

`\\servername\foldername`

If you are running Flax as a Windows Service, you will also need to make sure the Service has suitable account details to access the share. Flax is installed by default to use the 'Local System' account, which won't usually be able to access shared folders.

To change the account that Flax uses, select Administrative Tools from the Control Panel, then the Services applet. Find the Flax Service and right-click, then select Properties and the Logon tab. Check the 'This account' radio button and enter a suitable username and password (i.e., one that is allowed to access the shared folder you are trying to index). Click OK. You will then have to restart the Flax Service - right-click and select 'Stop', then right-click and select 'Start'.

Note that in some situations you (or your network administrator) may want to create a special user account for Flax that can access all the files you wish to search.


**Why can't I index RTF documents on Windows 2000?**

Windows 2000 does not include the IFilter for RTF documents, which is included with later versions of Windows. You may thus see some errors while indexing such as 'Unable to access object.' You can install the RTF IFilter from http://download.microsoft.com/download/SharePointPortalServer/Utility/1/NT5/EN-US/RTF.exe  Run the program to unzip the files and copy the `rtffilt.dll` file to `C:\windows\system32` (or `C:\winnt\system32`), then register it by running _Start_, _Run_, `regsvr32 rtffilt.dll`. Flax Basic should now index RTF files correctly.

**Why can't I index HTML documents on Windows 2000 Server?**

Windows 2000 Server does not seem to register the HTML IFilter correctly. Stop indexing, register the IFilter by running _Start_, _Run_, `regsvr32 nlhtml.dll`, and restart indexing - the indexing should now work correctly. Note: the Flax Basic installation process attempts to perform this process automatically.

**Why can't I index PDF documents?**

You may not have the correct IFilter for Adobe Acrobat (PDF) documents installed. This IFilter is included with Acrobat Reader and is also available seperately from Adobe; you can download it from http://download.adobe.com/pub/adobe/acrobat/win/all/ifilter60.exe. After installing this program Flax Basic will be able to install PDF documents.

We have had some reports that the Adobe IFilter installed with Adobe Reader 8 is more reliable - you can obtain Adobe Reader 8 from http://www.adobe.com

**Why can't I index Office 2007 documents?**

This feature was added to Flax Basic for version 1.1, please make sure you are using the newest version. Also, you may not have the correct IFilter for Office 2007 installed. You can download a filter pack from
http://www.microsoft.com/downloads/details.aspx?FamilyId=60C92A37-719C-4077-B5C6-CAC34F4227CC&displaylang=en
After installing this program Flax Basic will be able to index Office 2007 documents.

**How fast can I build my indexes?**

This will depend on what types of files you want to index. In general, using the IFilter system, indexing PDF files is slowest, and indexing plain text and HTML is fastest. The speed of indexing will also depend on the speed of your system and how much memory is available.

**I've seen some errors while indexing, what does this mean?**

This means that Flax Basic could not extract the text from some of the files it found (you should also notice that the number of Documents reported by the Collection Status page is less than the number of Files). To see more detail about the error check the indexer log file, which is found at `C:\Program Files\Flax Basic\logs\flaxindexer.log` (assuming you installed Flax Basic to the default folder). Look for a line such as:

`<date> <time>,700: ERROR: Filtering file: <a path to a file> with filter: `

You should then try and open the file specified by <a path to a file> in an appropriate program (i.e., if it is a PDF file try opening it in Acrobat). The file may be malformed or have the wrong extension (i.e. an Excel file saved as .doc) or there may be other errors that prevent the IFilter system from reading it.

**How can I see more detail about the indexing process?**

You can change the logging level for the indexing process using the Options page. For example, change the level to INFO to see when the indexing process starts and stops; change it to DEBUG to see when the process indexes each particular file. Note that the higher the log level, the more messages are generated, so the log file can get very large!

**I've seen some errors while indexing PDF files, what does this mean? I have the PDF IFilter installed correctly.**

The Adobe IFilter sometimes reports errors while reading certain PDF files. Flax Basic attempts to work around this by reading as much of the rest of the file as possible.

We have had some reports that the Adobe IFilter installed with Adobe Reader 8 is more reliable - you can obtain Adobe Reader 8 from http://www.adobe.com

**I've seen some other errors, how can I report them and/or find a solution?**

If you have seen other errors while using Flax, please visit http://www.flax.co.uk to report them. We will endeavour to provide fixes and workarounds and will use the information to contribute to Flax's ongoing improvement.

**My indexing stopped unexpectedly!**

It's possible that you ran out of disk space while indexing. You will have set a folder for Flax Basic to use for data files at installation time. First, make sure Flax Basic is not running. If you installed Flax Basic as a Service, you can stop it by running the file `C:\Program Files\Flax Basic\stopflaxservice.bat`, if it is running in a command window then close that window. Then you will need to edit the Windows Registry (take care as you can damage your Windows system if this is not done correctly).

Open a command window (_Start_, _Run_, `cmd`) and type:

`regedit`

Open the registry setting at:

`HKEY_LOCAL_MACHINE\SOFTWARE\Lemur Consulting Ltd\Flax Basic\DataPath`

and change this to a folder on a disk drive with enough space. As a rule of thumb, the databases created by Flax will be at least as big as the source files you want to search.

Close the Registry editor and restart the Flax Basic service if necessary by running the file `C:\Program Files\Flax Basic\startflaxservice.bat`, or run the Flax Basic (Manual Start) program from the Programs menu.

**I tried to create a collection but got an error 'A collection of this name is currently being deleted'**

You will have previously deleted a collection of the same name, and the previous collection is still be cleared up - possibly because someone else is still searching it. Either use a different name for the new collection or restart Windows (on startup the old collection will be removed).

## Troubleshooting ##

**I have found another problem, how do I find out more and report it?**

If you are running Flax as a Windows Service, please check the Event Log to see if a problem has been reported (you can find this in _Start_, _Control Panel_, _Administrative Tools_). Check the Application Log for messages about Flax.

You should also check the Flax log files. These are located in the `/logs` subfolder of the Flax installation folder (usually `C:\Program Files\Flax Basic`).

You can contact us via http://www.flax.co.uk.