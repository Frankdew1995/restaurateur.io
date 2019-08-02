<?php

$orderPath="order/".$_GET['shopName']."/".$_GET['table'];
$file=$orderPath."/orderInfo.txt";

if (! file_exists ( $file )) {
    mkdir ( "$file", 0777, true );
}

echo file_get_contents($file);