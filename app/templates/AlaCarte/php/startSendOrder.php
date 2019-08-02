<?php
/**
 * Created by PhpStorm.
 * User: juhaodong
 * Date: 2018/6/20
 * Time: 10:04
*/
//请设置每两分钟在服务器端执行一次的定时任务以便使用。

$url="http://www.xstargroup.de/JapanBuffet/php/menuDataByXSTAR.php?q=sendOrder";
echo file_get_contents($url);
?>

