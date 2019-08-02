<?php
$orderPath="order/".$_GET['shopName']."/".$_GET['table'];
//echo $orderPath;
if(!file_exists($orderPath)){
    mkdir($orderPath,0777,true) or die("can not make dir");
}

$file=fopen($orderPath."/orderInfo.txt","w") or die($orderPath."orderInfo.txt");
$order=$_GET['order'];
fwrite($file,$order);



echo 'good';




