<?php

header("Content-type: image/jpg");
echo file_get_contents("digits/" . $_SERVER['QUERY_STRING'] . ".jpg");

?>

