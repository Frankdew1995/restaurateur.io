<?php
//选择数据库
//mysqli_select_db($conn, $db_name) or die('选择数据库失败！');

$name=$_POST['name'];
$price=$_POST['price'];
$type=$_POST['type'];
$fileName= $_FILES["file"]["name"];

if ($_FILES["file"]["error"] > 0)
{
    echo "Return Code: " . $_FILES["file"]["error"] . "<br />";
    return;
}
else
{


    if (file_exists("../resource/image/" . $_FILES["file"]["name"]))
    {
        echo $_FILES["file"]["name"] . " already exists. ";
    }
    else
    {
        move_uploaded_file($_FILES["file"]["tmp_name"],
            "../resource/image/" . $_FILES["file"]["name"]);

    }
}

$sql="INSERT INTO `u822253106_xstar`.`menu` (`id`, `name`, `price`, `type`, `imagename`) VALUES ('', '".$name."', '".$price."', '".$type."', '".$fileName."');";
mysqli_query($conn,$sql);
mysqli_close($conn);

echo "添加成功，图片保存在: " . "../resource/image/" . $_FILES["file"]["name"]. "<br><a  style='background:black;color:white;font-size: 30px' href='../html/Server/html/dishAdd.html'>返回</a>";
