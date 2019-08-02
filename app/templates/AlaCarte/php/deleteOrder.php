<?php

$order=json_decode( $_GET['order']);
$orderPath="order/".$order->shopName."/".$order->table;
$file=$orderPath."/orderInfo.txt";
unlink($file);
