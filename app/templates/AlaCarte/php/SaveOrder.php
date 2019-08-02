<?php
//echo "hello world";
$order=json_decode( $_GET['Order']);
echo json_encode($order);

$email="contact@jhdsoftware.com";
$subject="print";
$message="";
$message.="Xstar\n"."tableNumber：".$order->tableID."\n";
$s="";
$s.="=============================\n";
foreach ($order->info as $value){


        $s.=$value->name."----------".$value->price."\n";
        $s.=" x".$value->amount."\n";


}
$s.="=============================\n";
$s.="Count:".$order->count;
$s.="Summe:".$order->price;
$message.=$s;
//echo "good";

mail($email,$subject,$message);

