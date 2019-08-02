<?php


$order=json_decode( $_GET['order']);

$email="haodong.ju@asiagourment.de";
$subject="print";
$message="";
$message.=$order->shopName."\n"."tableNumber：".$order->table."\n";
$s="";
$s.="=============================\n";
foreach ($order->info as $value){
    $s.=$value->name."----------".$value->price."\n";
}
$s.="=============================\n";
$s.="Summe:".$order->price;
$message.=$s;
mail($email,$subject,$message);
