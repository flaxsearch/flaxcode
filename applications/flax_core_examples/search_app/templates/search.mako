<%! 
    from lxml import etree
%>

<%inherit file="/base.mako" />

<%def name="head_tags()">
    <script type="text/javascript">
        function clearfac() {
            var cb = document.getElementsByName("authfac");
            for (var i = 0; i < cb.length; i++) {
                cb[i].checked = false;
            }
            document.forms[0].submit();
        }
    </script>
</%def>

<h1>flax.core simple search</h1>

<form method="GET">
    Query: <input id="query" name="query" value="${query}" />
    &nbsp;&nbsp;    
    Year:
    <select name="yearfrom">
        <option value="">Any</option>
        % for yr in xrange(1700, 2020, 10):
            % if str(yr) == yearfrom:
                <option selected>${yr}</option>
            % else:
                <option>${yr}</option>
            % endif
        % endfor
    </select>
    to
    <select name="yearto">
        <option value="">Any</option>
        % for yr in xrange(1700, 2020, 10):
            % if str(yr) == yearto:
                <option selected>${yr}</option>
            % else:
                <option>${yr}</option>
            % endif
        % endfor
    </select>
        
    <input type="submit" value="Search" />
    
    % if results.size():
    
        <p>
            <h3>Author facet:</h3>
            % for author in results.facets['author']:
            <%
                author = author.decode('utf-8', 'ignore')
                checked = ''
                if author in authfac:
                    checked = 'checked'
            %>
                <input type="checkbox" name="authfac" value="${author}" ${checked}/>
                ${author} <br/>
            % endfor
            <a href="javascript:clearfac()">clear</a>
        </p>
    
        <h2>
            ${results.get_firstitem() + 1} - 
            ${results.get_firstitem() + results.size()} of
            % if results.get_matches_estimated() != results.get_matches_lower_bound():
                about
            % endif
            ${results.get_matches_estimated()} results
        </h2>
        
        % for hit in results:
        <% 
            data = hit.document.get_data().decode('utf-8', 'ignore')
            root = etree.fromstring(data)
            title = root.xpath("//metadata[@name='Title']/@value")[0]
            author = root.xpath("//metadata[@name='Author']/@value")[0]
            year = root.xpath("//metadata[@name='Year']/@value")[0]
            sample = root.xpath("//sample//text()")[0]
        %> 
            <div class="hit">
                <div class="title">${title} by ${author} (${year})</div>
                <div class="sample">${sample}</div>
            </div>
        % endfor

    % elif query:
        <h2>no results</h2>
    % endif
    
</form>