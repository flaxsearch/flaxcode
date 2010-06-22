<%inherit file="/base.mako" />

<%def name="head_tags()">
</%def>

<h1>flax.core simple search</h1>
<h2>pick a database:</h2>

% for db in dbs:
    <p><a href="/${db}/search">${db}</a></p>
% endfor