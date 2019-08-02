<?php

use PHPMailer\PHPMailer\PHPMailer;
use PHPMailer\PHPMailer\Exception;
 
require '../../reference/phpMailer/Exception.php';
require '../../reference/phpMailer/PHPMailer.php';
require '../../reference/phpMailer/SMTP.php';

$db_host = 'localhost';
//用户名
$db_user = 'DB_User_local';
//密码
$db_password = 'Zgz921^e';
//数据库名 
$db_name = 'v4_alacarte';


//端口
$db_port = '3306';
//连接数据库
$conn = new mysqli($db_host, $db_user, $db_password, $db_name);// or die('连接数据库失败！');
//echo json_encode($conn).'<br/>';
if ($conn->connect_error) {
    die("连接失败: " . $conn->connect_error);
}

//$WATER_BAR_MAIL_ADDRESS = 'support@xstargroup.eu';
$WATER_BAR_MAIL_ADDRESS = 'support@xstargroup.eu';
//$KITCHEN_MAIL_ADDRESS = 'support@xstargroup.eu';
$KITCHEN_MAIL_ADDRESS = 'support@xstargroup.eu';

$MAIL_LINE_LENGTH = 40;

$WATER = array('Getränke', 'Wein', 'Eis & Kaffee', 'Buffet');

//时区
date_default_timezone_set("Asia/Shanghai");
// date_default_timezone_set('Europe/Berlin');
class CacheLock
{
    //文件锁存放路径
    private $path = null;
    //文件句柄
    private $fp = null;
    //锁粒度,设置越大粒度越小
    private $hashNum = 100;
    //cache key 
    private $name;
    //是否存在eaccelerator标志
    private  $eAccelerator = false;
    
    /**
     * 构造函数
     * 传入锁的存放路径，及cache key的名称，这样可以进行并发
     * @param string $path 锁的存放目录，以"/"结尾
     * @param string $name cache key
     */
    public function __construct($name,$path='lock/')
    {
        //判断是否存在eAccelerator,这里启用了eAccelerator之后可以进行内存锁提高效率
        $this->eAccelerator = function_exists("eaccelerator_lock");
        if(!$this->eAccelerator)
        {
            $this->path = $path.($this->_mycrc32($name) % $this->hashNum).'.txt';
        }
        $this->name = $name;
    }
    
    /**
     * crc32
     * crc32封装
     * @param int $string
     * @return int
     */
    private function _mycrc32($string)
    {
        $crc = abs (crc32($string));
        if ($crc & 0x80000000) {
            $crc ^= 0xffffffff;
            $crc += 1;
        }
        return $crc;
    }
    /**
     * 加锁
     * Enter description here ...
     */
    public function lock()
    {
        //如果无法开启ea内存锁，则开启文件锁
        if(!$this->eAccelerator)
        {
            //配置目录权限可写
            $this->fp = fopen($this->path, 'w+');
            if($this->fp === false)
            {
                return false;
            }
            return flock($this->fp, LOCK_EX);
        }else{
            return eaccelerator_lock($this->name);
        }
    }
    
    /**
     * 解锁
     * Enter description here ...
     */
    public function unlock()
    {
        if(!$this->eAccelerator)
        {
            if($this->fp !== false)
            {
                flock($this->fp, LOCK_UN);
                clearstatcache();
            }
            //进行关闭
            fclose($this->fp);
        }else{
            return eaccelerator_unlock($this->name);
        }
    }
}
class SqlSelect
{
    private $columns;
    private $table;
    private $predicates;
    private $sql;
    private $conn;

    public function __construct(mysqli $conn, array $columns, $table, array $predicates = null, $after_where = null)
    {
        $this->conn = $conn;
        $this->columns = $columns;
        $this->table = $table;
        $this->predicates = $predicates;

        $this->sql =
            'SELECT ' . join(', ', $this->columns) .
            ' FROM ' . $this->table .
            ($this->predicates == null ? '' : ' WHERE (' . join(' AND ', $this->predicates) . ")") .
            ($after_where ?? '') . ';';
    }

    public function get_sql()
    {
        return $this->sql;
    }


    /**
     * @return array
     */
    public function excecuteSql()
    {
        // echo $this->sql;
        $query_result = $this->conn->query($this->sql);
        //echo $query_result->num_rows;
        $result = array();
        while ($row = $query_result->fetch_assoc()) {
            array_push($result, $row);
        }
        return $result;
    }
}

class SqlInsert
{
    private $columns;
    private $table;
    private $values;
    private $sql;
    private $conn;

    public function __construct(mysqli $conn, $table, array $columns, array $values)
    {
        $this->conn = $conn;
        $this->columns = $columns;
        $this->table = $table;
        $this->values = $values;

        $this->sql =
            "INSERT INTO " . $table .
            " (" . join(", ", $columns) . ") VALUES (" . join(", ", $this->values) . ");";
    }

    public function get_sql()
    {

        return $this->sql;
    }


    /**
     * @return bool|mysqli_result
     */
    public function excecuteSql()
    {
        //echo $this->sql;
        $query_result = $this->conn->query($this->sql);
        return $query_result;
    }
}

class SqlUpdate
{
    private $column_value_pairs;
    private $table;
    private $sql;
    private $conn;
    private $predicates;

    public function __construct(mysqli $conn, $table, array $column_value_pairs, array $predicates)
    {
        $this->conn = $conn;
        $this->column_value_pairs = $column_value_pairs;
        $this->table = $table;
        $this->predicates = $predicates;
        $sub_sentences = array();
        foreach ($column_value_pairs as $column => $value) {
            array_push($sub_sentences, ($column . "=" . $value));
        }

        $this->sql =
            "UPDATE " . $table .
            " SET " . join(", ", $sub_sentences) .
            " WHERE (" . join(" AND ", $predicates) . ");";

    }

    public function get_sql()
    {
        return $this->sql;
    }


    /**
     * @return bool|mysqli_result
     */
    public function excecuteSql()
    {
        //echo $this->sql;
        $query_result = $this->conn->query($this->sql);
        return $query_result;
    }
}

class SqlDelete
{
    private $table;
    private $sql;
    private $conn;
    private $predicates;

    public function __construct(mysqli $conn, $table, array $predicates)
    {
        $this->conn = $conn;
        $this->table = $table;
        $this->predicates = $predicates;

        $this->sql =
            "DELETE FROM " . $table .
            " WHERE (" . join(" AND ", $predicates) . ");";

    }

    public function get_sql()
    {
        return $this->sql;
    }


    /**
     * @return bool|mysqli_result
     */
    public function excecuteSql()
    {
        //echo $this->sql;
        $query_result = $this->conn->query($this->sql);
        return $query_result;
    }
}

function get_dish_name_by_id(mysqli $conn, $dish_id)
{
    $sql_select = new SqlSelect($conn,
        array("name"),
        'Dishes',
        array(sprintf("dishId='%s'", $dish_id)));
    return $sql_select->excecuteSql();
}

function get_dish_detail_by_id(mysqli $conn, $dish_id)
{
    $sql_select = new SqlSelect($conn,
        array("*"),
        'Dishes',
        array(sprintf("dishId='%s'", $dish_id)));
    return $sql_select->excecuteSql();
}

//timespan(0: daycount, 1: today, 2: this week, 3:this month, 4: this year), [daycount=0]
function get_day_count($timespan, $daycount = 0)
{
    switch ($timespan) {
        case 4:
            return (int)date('z');

        case 3:
            return (int)date('j');

        case 2:
            return (int)date('N');

        case 1:
            return 0;

        default:
        case 0:
            return (int)$daycount;
    }
}

function get_predicate_by_day_count($day_count, $end_date = null)
{
    return sprintf("date%s",
        $day_count > 0
            ? sprintf(" BETWEEN DATE_SUB('%s', INTERVAL %d DAY) AND '%s'",
            ($end_date ?? date('Y-m-d')), $day_count, ($end_date ?? date('Y-m-d')))

            : sprintf("='%s'", ($end_date ?? date('Y-m-d'))));
}

function send_mail($to, $subject, $body)
{
    $mail = new PHPMailer(true);                      // Passing `true` enables exceptions
    try {
        //Server settings
        //$mail->SMTPDebug = 2;                                 // Enable verbose debug output
        $mail->isSMTP();                                        // Set mailer to use SMTP
        $mail->Host = 'xstargroup.eu';                          // Specify main and backup SMTP servers
        $mail->SMTPAuth = true;                                 // Enable SMTP authentication
        $mail->Username = 'support@xstargroup.eu';                // SMTP username
        $mail->Password = 'Zgz921^e';                         // SMTP password
        $mail->SMTPSecure = 'tls';                              // Enable TLS encryption, `ssl` also accepted
        $mail->Port = 587;                                      // TCP port to connect to

        //Recipients
        $mail->setFrom('support@xstargroup.eu', 'XSTAR Support');
        $mail->addAddress($to);                             // Add a recipient
        //$mail->addAddress('ellen@example.com');               // Name is optional
        //$mail->addReplyTo('info@example.com', 'Information');
        //$mail->addCC('cc@example.com');
        //$mail->addBCC('bcc@example.com');

        //Attachments
        //$mail->addAttachment('/var/tmp/file.tar.gz');         // Add attachments
        //$mail->addAttachment('/tmp/image.jpg', 'new.jpg');    // Optional name

        //Content
        $mail->isHTML(false);                                  // Set email format to HTML
        $mail->Subject = $subject;
        $mail->Body = $body;
        //$mail->AltBody = $body;

        $mail->send();
        //echo 'Message has been sent';
    } catch (Exception $e) {
        echo 'Message could not be sent. Mailer Error: ', $mail->ErrorInfo;
    }
}

$q_paramter = $_GET['q'];
$page = 1;
$pageSize = 15;
if(isset($_GET["page"])){ 
    $page = $_GET['page'];
} 
switch ($q_paramter) {
    //using parameter: table
    case 'getAllData':
        $sql_select = new SqlSelect($conn, array("*"), $_GET['table']);

        echo json_encode($sql_select->excecuteSql());
        break;
    //堂食打印
    case 'getFoodPrint1':
        $sql_select = new SqlSelect($conn, array("id","ordertime","tablename","seat","name","Chinesename","amount"), 
            "printline_food",array("ptype=1","isprint=0"),
            " order by ordertime asc limit 10");
        $result = $sql_select->excecuteSql();
        echo json_encode($result);

        //遍历id
        $ids = array();
        foreach ($result as $value){
            $id = $value['id'];
            array_push($ids, $id);
        }
        //更新，设置已打印
        $sql_update = new SqlUpdate($conn, 'printline_food',array('isprint' => 1),array(sprintf("id in (%s)",join(", ", $ids))) );
        $sql_update->excecuteSql();
        //echo $sql_update->get_sql();
        break;
    //堂食打印 1_1 前台
    case 'getFoodPrint1_1':
        $sql_select = new SqlSelect($conn, array("id","ordertime","tablename","seat","name","Chinesename","amount"), 
            "printline_food",array("ptype=1","isprint=0","reception_kitchen=1"),
            " order by ordertime asc limit 10");
        $result = $sql_select->excecuteSql();
        echo json_encode($result);

        //遍历id
        $ids = array();
        foreach ($result as $value){
            $id = $value['id'];
            array_push($ids, $id);
        }
        //更新，设置已打印
        $sql_update = new SqlUpdate($conn, 'printline_food',array('isprint' => 1),array(sprintf("id in (%s)",join(", ", $ids))) );
        $sql_update->excecuteSql();
        //echo $sql_update->get_sql();
        break;
    //堂食打印 1_2 厨房
    case 'getFoodPrint1_2':
        $sql_select = new SqlSelect($conn, array("id","ordertime","tablename","seat","name","Chinesename","amount"), 
            "printline_food",array("ptype=1","isprint=0","reception_kitchen=2"),
            " order by ordertime asc limit 10");
        $result = $sql_select->excecuteSql();
        echo json_encode($result);

        //遍历id
        $ids = array();
        foreach ($result as $value){
            $id = $value['id'];
            array_push($ids, $id);
        }
        //更新，设置已打印
        $sql_update = new SqlUpdate($conn, 'printline_food',array('isprint' => 1),array(sprintf("id in (%s)",join(", ", $ids))) );
        $sql_update->excecuteSql();
        //echo $sql_update->get_sql();
        break;
    //外卖打印
    case 'getFoodPrint2':
        $sql_select = new SqlSelect($conn, array("tablename","ordertime"), 
            "printline_food",array("ptype=2","isprint=0"),
            "group by tablename order by ordertime asc limit 5");
        $result = $sql_select->excecuteSql();
        echo json_encode($result);

        //遍历id
        $tablenames = array();
        foreach ($result as $value){
            $tablename = sprintf("'%s'", $value['tablename']);
            array_push($tablenames, $tablename);
        }
        //更新，设置已打印
        $sql_update = new SqlUpdate($conn, 'printline_food',array('isprint' => 1),
            array(sprintf("tablename in (%s)",join(", ", $tablenames))));
        $sql_update->excecuteSql();
        //echo $sql_update->get_sql();
        break;
        //外卖打印 2_1 前台打印
    case 'getFoodPrint2_1':
        $sql_select = new SqlSelect($conn, array("tablename","ordertime"), 
            "printline_food",array("ptype=2","isprint=0","reception_kitchen=1"),
            "group by tablename order by ordertime asc limit 5");
        $result = $sql_select->excecuteSql();
        echo json_encode($result);

        //遍历id
        $tablenames = array();
        foreach ($result as $value){
            $tablename = sprintf("'%s'", $value['tablename']);
            array_push($tablenames, $tablename);
        }
        //更新，设置已打印
        $sql_update = new SqlUpdate($conn, 'printline_food',array('isprint' => 1),
            array(sprintf("tablename in (%s)",join(", ", $tablenames))));
        $sql_update->excecuteSql();
        //echo $sql_update->get_sql();
        break;
    //外卖打印 2_2 厨房打印
    case 'getFoodPrint2_2':
        $sql_select = new SqlSelect($conn, array("tablename","ordertime"), 
            "printline_food",array("ptype=2","isprint=0","reception_kitchen=2"),
            "group by tablename order by ordertime asc limit 5");
        $result = $sql_select->excecuteSql();
        echo json_encode($result);

        //遍历id
        $tablenames = array();
        foreach ($result as $value){
            $tablename = sprintf("'%s'", $value['tablename']);
            array_push($tablenames, $tablename);
        }
        //更新，设置已打印
        $sql_update = new SqlUpdate($conn, 'printline_food',array('isprint' => 1),
            array(sprintf("tablename in (%s)",join(", ", $tablenames))));
        $sql_update->excecuteSql();
        //echo $sql_update->get_sql();
        break;
    //呼叫服务员打印
    case 'getServicePrint':
        $sql_select = new SqlSelect($conn, array("id","tablename","seat","calltime"), 
            "printline_service",array("isprint=0"),
            " order by calltime asc limit 10");
        $result = $sql_select->excecuteSql();
        echo json_encode($result);

        //遍历id
        $ids = array();
        foreach ($result as $value){
            $id = $value['id'];
            array_push($ids, $id);
        }
        //更新，设置已打印
        $sql_update = new SqlUpdate($conn, 'printline_service',array('isprint' => 1),array(sprintf("id in (%s)",join(", ", $ids))) );
        $sql_update->excecuteSql();
        //echo $sql_update->get_sql();
        break;
    //结账单打印
    case 'getOrderPrint':
        $sql_select = new SqlSelect($conn, array("id","ordertime","orderId","tablename","amount"), 
            "printline_order",array("isprint=0"),
            " order by ordertime asc limit 5");
        $result = $sql_select->excecuteSql();
        echo json_encode($result);

        //遍历id
        $ids = array();
        foreach ($result as $value){
            $id = $value['id'];
            array_push($ids, $id);
        }
        //更新，设置已打印
        $sql_update = new SqlUpdate($conn, 'printline_order',array('isprint' => 1),array(sprintf("id in (%s)",join(", ", $ids))) );
        $sql_update->excecuteSql();
        //echo $sql_update->get_sql();
        break;
    //堂食打印
    case 'getPrint1':
        $id = $_POST['id'];
        $sql_select = new SqlSelect($conn, array("*"), 
            "printline_food",array(sprintf("id=%d",$id)));
        $result = $sql_select->excecuteSql();
        echo json_encode($result);
        break;
    //外卖打印
    case 'getPrint2':
        $tablename = $_POST['id'];
        $sql_select = new SqlSelect($conn, array("*"), 
            "printline_food",array(sprintf("tablename='%s'",$tablename)));
        $result = $sql_select->excecuteSql();
        echo json_encode($result);
        break;
    //账单打印
    case 'getPrint3':
        $data = array();
        //订单
        $id = $_POST['id'];
        $sql_select = new SqlSelect($conn, array("printline_order.*,paymentmethod"), 
            "printline_order,".$db_name.".order",array(sprintf("printline_order.id=%d",$id),sprintf("printline_order.orderId=%s.order.orderId",$db_name)));
        $result = $sql_select->excecuteSql();

        //详细
        $orderId = $result[0]['orderId'];
        $sql_select1 = new SqlSelect($conn, array("*"), 
            "dishlog",array(sprintf("orderId='%s'",$orderId)));
        $result1 = $sql_select1->excecuteSql();
        //餐馆信息
        $sql_select2 = new SqlSelect($conn, array("*"), "info",array());
        $result2 = $sql_select2->excecuteSql();

        array_push($data, $result2);
        array_push($data, $result);
        array_push($data, $result1);

        echo json_encode($data);
        break;
    //服务打印
    case 'getPrint4':
        $id = $_POST['id'];
        $sql_select = new SqlSelect($conn, array("*"), 
            "printline_service",array(sprintf("id=%d",$id)));
        $result = $sql_select->excecuteSql();
        echo json_encode($result);
        break;
    //桌子数据
    case 'getTableIndex':
        $tableType = $_GET['tableType'];
        $sql_select = new SqlSelect($conn, array("id","tablename as 桌名","tablenr","seatCount as 座位数","grouping as 分区"), 'TableIndex',array(sprintf("tableType=%s",  $tableType) ));
        echo json_encode($sql_select->excecuteSql());
        break;
    //获取自助餐
    case 'getBuffet':
        $sql_select = new SqlSelect($conn, array("id","name as 菜品名","Chinesename as 中文名" ,"price as 午餐价格" ,"price_pm as 晚餐价格" ,"price567 as 节假日午餐价格","price567_pm as 节假日晚餐价格" ,"discribe as 描述","imagename as 图片"), $_GET['table'],array("type='Buffet'","price!=0"));

        echo json_encode($sql_select->excecuteSql());
        break;
    //获取菜品
    case 'getDishes':
         //总记录数
        $count_select = new SqlSelect($conn, array("count(*) as count"), 'Dishes',array("type!='Buffet'"));
        $count = $count_select->excecuteSql()[0]['count'];

        $sql_select = new SqlSelect($conn, array("id","name as 菜品名","Chinesename as 中文名" ,"price as 价格" ,"type as 分类","type2 as 类型"  ,"discribe as 描述","imagename as 图片"), 'Dishes',array("type!='Buffet'"),"order by id desc limit " . (($page-1)*$pageSize).",".$pageSize.";");
        $dish = $sql_select->excecuteSql();

        //分页显示数据
        $result = array();
        array_push($result,$dish);

        $pageInfo['count'] = $count;
        $pageInfo['pageSize'] = $pageSize;
        $pageInfo['page'] = $page - 1;

        array_push($result,$pageInfo);

        echo json_encode($result);
        break;
    //获取菜品
    case 'getPrintFood':
         //总记录数
        $count_select = new SqlSelect($conn, array("count(*) as count"), 'printline_food',array("isprint=1"));
        $count = $count_select->excecuteSql()[0]['count'];

        $sql_select = new SqlSelect($conn, array("id","ordertime as 下单时间","tablename as 桌名","seat as 座位号","name as 菜名","Chinesename as 中文名","amount as 数量"), 'printline_food',array("isprint=1"),"order by id desc limit " . (($page-1)*$pageSize).",".$pageSize.";");
        $dish = $sql_select->excecuteSql();

        //分页显示数据
        $result = array();
        array_push($result,$dish);

        $pageInfo['count'] = $count;
        $pageInfo['pageSize'] = $pageSize;
        $pageInfo['page'] = $page - 1;

        array_push($result,$pageInfo);

        echo json_encode($result);
        break;
    //获取菜品
    case 'getPrintOrder':
         //总记录数
        $count_select = new SqlSelect($conn, array("count(*) as count"), 'printline_order',array("isprint=1"));
        $count = $count_select->excecuteSql()[0]['count'];

        $sql_select = new SqlSelect($conn, array("id","ordertime as 结账时间","orderId as 订单号","tablename as 桌名","amount as 金额"), 'printline_order',array("isprint=1"),"order by id desc limit " . (($page-1)*$pageSize).",".$pageSize.";");
        $dish = $sql_select->excecuteSql();

        //分页显示数据
        $result = array();
        array_push($result,$dish);

        $pageInfo['count'] = $count;
        $pageInfo['pageSize'] = $pageSize;
        $pageInfo['page'] = $page - 1;

        array_push($result,$pageInfo);

        echo json_encode($result);
        break;
    //重新打印food
    case 'updatePrintFood':
        $updateArr = array();
        $updateArr['isprint'] = 0;

        $sql_update = new SqlUpdate($conn, 'printline_food',$updateArr,array(sprintf("id in (%s)", $_POST['ids'])));
        $result = $sql_update->excecuteSql();

        if ($result === true) {
            echo "ok";
        } else {
            echo "Error on: " . $sql_update->get_sql() . "<br>" . $conn->error . "<br>";
        }

        break;
    //重新打印Order
    case 'updatePrintOrder':
        $updateArr = array();
        $updateArr['isprint'] = 0;

        $sql_update = new SqlUpdate($conn, 'printline_order',$updateArr,array(sprintf("id in (%s)", $_POST['ids'])));
        $result = $sql_update->excecuteSql();

        if ($result === true) {
            echo "ok";
        } else {
            echo "Error on: " . $sql_update->get_sql() . "<br>" . $conn->error . "<br>";
        }

        break;
    //获取订单2
    case 'getOrder2':
        $tableItems = array();
        //读取所有餐中订单，循环读取所有table表的数据，加入到array
        $sql_select = new SqlSelect($conn, array("tablenr","tablename"), 'tableindex',array("isUsing = 1"),"order by tablenr asc");
        $UsingTable = $sql_select->excecuteSql();
        foreach ($UsingTable as  $table) {
            $table_ = "Table_" . $table['tablenr'];
            $sql_select_table = new SqlSelect($conn, 
                array( $table_.".dishId as 桌子", $table_.".dishname as 菜品","Chinesename as 中文名", $table_.".price as 价格","amount as 数量","seat as 桌位","`timestamp` as 下单时间"), 
                $table_.",dishes",
                array($table_.".price >= 0 and " .$table_.".dishId = dishes.dishId"),
                "order by seat asc, `timestamp` asc"
            );

            $result = $sql_select_table->excecuteSql();
            $r = array();
            foreach ($result as $value) {
                $value['桌子'] = $table['tablename'];
                array_push($r,$value);
            }

            array_push($tableItems,$r);
        }

        echo json_encode($tableItems);
        break;

    //获取订单3 外卖
    case 'getOrder3':
        $tableItems = array();
        //读取所有status = 1（已完成） 的订单  
        //总记录数
        $count_select = new SqlSelect($conn, array("count(*) as count"), $db_name . '.Order',array("status = 1"));
        $count = $count_select->excecuteSql()[0]['count'];
        
        $sql_select = new SqlSelect($conn, array("*"), $db_name . '.Order',array("status = 1"),"order by `timestamp` desc limit " . (($page-1)*$pageSize).",".$pageSize.";");
        $UsingTable = $sql_select->excecuteSql();
        foreach ($UsingTable as  $table) {
            $sql_select_table = new SqlSelect($conn, 
                array( "dishlog.dishname as 菜品","Chinesename as 中文名 ", "dishlog.price as 价格","amount as 数量"), 
                "dishlog,dishes",
                array("orderId ='" .$table['orderId']."' and dishlog.dishId = dishes.dishId"),
                "order by seat asc ,dishlog.id asc"
            );
            $result = $sql_select_table->excecuteSql();
            //echo $sql_select_table->get_sql();
            $order['订单号'] = $table['orderId'];
            $order['总金额'] = $table['amount'];
            $order['下单时间'] = $table['timestamp'];
            $order['订单状态'] = "已付款";
            $orderArr = array();
            array_push($orderArr,$order);
            array_push($tableItems,$orderArr);
            array_push($tableItems,$result);
        }
        $result = array();
        array_push($result,$tableItems);

        $pageInfo['count'] = $count;
        $pageInfo['pageSize'] = $pageSize;
        $pageInfo['page'] = $page - 1;

        array_push($result,$pageInfo);

        echo json_encode($result);
        break;


    //using parameter:
    case 'getMenuInfo':
        $sql_select = new SqlSelect($conn, array("*"), "MenuInfo");
        echo json_encode($sql_select->excecuteSql());
        break;
    //using parameter:
    case 'getMenuInfo1':
        $sql_select = new SqlSelect($conn, array("id","typename as 名称","countunit as 计量单位","type2 as 类型"), "MenuInfo");
        echo json_encode($sql_select->excecuteSql());
        break;
    //using parameter: dishId
    case 'getDishDetailById':

        echo json_encode(get_dish_detail_by_id($conn, $_GET['dishId']));
        break;

    //using parameter: dishId
    case 'getNameByDishId':
        echo json_encode(get_dish_name_by_id($conn, $_GET['dishId']));
        break;

    //using parameter: timespan(0: daycount, 1: today, 2: this week, 3:this month, 4: this year), [daycount=0]
    case 'getOrder':
        $day_count = get_day_count($_GET['timespan'], $_GET['daycount']);
        $group_string_name = "";
        $group_string = "";

        if($_GET['timespan'] == "1"){
            $group_string_name = "tablearea as 日结";
            $group_string = "tablearea";
        }
        if($_GET['timespan'] == "2"){
            $group_string_name = "DATE_FORMAT(`date`,'%W') as 周结";
            $group_string = "`date`";
        }
        if($_GET['timespan'] == "3"){
            $group_string_name = "DATE_FORMAT(`date`,'%m-%d') as 月结";
            $group_string = "`date`";
        }
        if($_GET['timespan'] == "4"){
            $group_string_name = "date_format(`date`, '%Y-%m') as 年结";
            $group_string = "date_format(`date`, '%Y-%m')";
        }
        $sql_select = new SqlSelect($conn, array($group_string_name ,"paymentmethod as 付账方式","sum(amount) as amount"), $db_name . '.Order',
            array(get_predicate_by_day_count($day_count),"status=1"),"group by ".$group_string.",paymentmethod");
        echo json_encode($sql_select->excecuteSql());
        break;

    //using parameter: tablenr, (int)usingSended
    case 'getAllDishesInTable':
        $table_nr = (int)$_GET['tablenr'];
        $usingSended = (int)$_GET['usingSended'];
        $sql_select = new SqlSelect($conn, array('*'), sprintf('Table_%04d', $table_nr),
            ($usingSended ? array('sended=0') : null));
        $result = $sql_select->excecuteSql();
        echo json_encode($result);
        break;

    //using parameter:
    case 'getJapanBuffetInfo':
        echo (new SqlSelect($conn, array('*'), 'JapanBuffetInfo',
            array('id=(SELECT MAX(id) FROM JapanBuffetInfo)')))->excecuteSql()[0];
        break;

    //餐馆设置
    case 'getInfo':
        echo json_encode( (new SqlSelect($conn, array('*'), 'Info'))->excecuteSql()[0]);
        break;

    //餐馆设置
    case 'updateInfo':
        $updateArr = array();
        if ($_POST['name'] != "") {
            $updateArr['name'] = sprintf("'%s'",  $_POST['name']);
        }
        if ($_POST['address'] != "") {
            $updateArr['address'] = sprintf("'%s'",  $_POST['address']);
        }
        if ($_POST['email'] != "") {
            $updateArr['email'] = sprintf("'%s'",  $_POST['email']);
        }
        if ($_POST['phone'] != "") {
            $updateArr['phone'] = sprintf("'%s'",  $_POST['phone']);
        }
        if ($_POST['tel'] != "") {
            $updateArr['tel'] = sprintf("'%s'",  $_POST['tel']);
        }
        if ($_POST['creatdate'] != "") {
            $updateArr['creatdate'] = sprintf("'%s'",  $_POST['creatdate']);
        }
        if ($_POST['city'] != "") {
            $updateArr['city'] = sprintf("'%s'",  $_POST['city']);
        }
        if ($_POST['country'] != "") {
            $updateArr['country'] =sprintf("'%s'",  $_POST['country']);
        }
        if ($_POST['postcode'] != "") {
            $updateArr['postcode'] = sprintf("'%s'",  $_POST['postcode']);
        }
         if ($_POST['website'] != "") {
            $updateArr['website'] = sprintf("'%s'",  $_POST['website']);
        }
        if ($_POST['texnumber'] != "") {
            $updateArr['texnumber'] = sprintf("'%s'",  $_POST['texnumber']);
        }
        
        $sql_update = new SqlUpdate($conn, 'Info',$updateArr,array(sprintf("id=%d", $_POST['id'])));
        $result = $sql_update->excecuteSql();

        if ($result === true) {
            echo "修改成功<br><a  style='background:black;color:white;font-size: 30px' href='../html/Server/settings.html'>返回</a>";
        } else {
            echo "Error on: " . $sql_update->get_sql() . "<br>" . $conn->error . "<br>";
        }

        break;

    //using parameter: tablenr, seat
    case 'getLastOrderInTable':
        $table_nr = $_GET['tablenr'];
        $seat = $_GET['seat'];
        echo (new SqlSelect($conn, array('MAX(timestamp)', 'type2'),
            sprintf('Table_%04d, Dishes', $table_nr),
            array(sprintf("(Table_%04d.dishId=Dishes.dishId)", $table_nr),
                "type2 = 'Food'",
                sprintf("seat=%d", $seat))
        ))->excecuteSql()[0]['MAX(timestamp)'];
        //->get_sql();

        break;

    //using parameter:
    case 'getIndexDataSet':
        $result = array();

        // 访问量和顾客量
        $seat_sum = (new SqlSelect($conn, array('date, SUM(seatCount)'), $db_name . '.Order, TableIndex',
            array("($db_name.Order.tablenr=TableIndex.tablenr)",
                '((date=DATE_SUB(CURDATE(), INTERVAL 1 DAY)) OR (date=CURDATE()))'),
            'GROUP BY date DESC'
        ))->excecuteSql();
        $today_access = 0;
        $yesterday_access = 0;
        if(count($seat_sum)>0){
            $today_access = $seat_sum[0]['SUM(seatCount)'];
        }
        if(count($seat_sum)>1){
            $yesterday_access = $seat_sum[1]['SUM(seatCount)'];
        }
        
        $access_ratio = 3;
        $result['access'] = array('today' => ((int)$today_access) * $access_ratio,
            'yesterday' => ((int)$yesterday_access) * $access_ratio);
        $result['customer'] = array('today' => (int)$today_access,
            'yesterday' => (int)$yesterday_access);

        //本日,昨日营业额
        $netto = (new SqlSelect($conn, array('date, SUM(amount)'), $db_name . '.Order',
            array('((date=DATE_SUB(CURDATE(), INTERVAL 1 DAY)) OR (date=CURDATE()))'),
            'GROUP BY date DESC'))->excecuteSql();
        $result['netto'] = array('today' => (int)($netto[0]['SUM(amount)'] ?? 1),
            'yesterday' => (int)($netto[1]['SUM(amount)'] ?? 1));

        //本月营业额
        $result['netto']['thisMonth'] = (int)((new SqlSelect($conn, array('SUM(amount)'), $db_name . '.Order',
                array(get_predicate_by_day_count(get_day_count(3)))))->excecuteSql()[0]['SUM(amount)'] ?? 1);

        //上月营业额
        $end_date = date_sub(date_create(),
            new DateInterval(sprintf('P%dD', get_day_count(3))));  // 上月最后一天
        $result['netto']['lastMonth'] = (int)((new SqlSelect($conn, array('SUM(amount)'), $db_name . '.Order',
                array(get_predicate_by_day_count((int)$end_date->format('j'), $end_date->format('Y-m-d'))))
            )->excecuteSql()[0]['SUM(amount)'] ?? 1);

        //本日详细
        $result['detail']['today'] = (new SqlSelect($conn,
            array("DATE_FORMAT(timestamp, '%Y-%m-%d %k:%i') AS period", 'amount', 'paymentMethod'),
            $db_name . '.Order',
            array('date=CURDATE()'),
            ' ORDER BY period'))->excecuteSql();

        //昨日详细
        $result['detail']['yesterday'] = (new SqlSelect($conn,
            array("DATE_FORMAT(timestamp, '%Y-%m-%d %k:%i') AS period", 'amount', 'paymentMethod'),
            $db_name . '.Order',
            array('date=DATE_SUB(CURDATE(), INTERVAL 1 DAY)'),
            ' ORDER BY period'))->excecuteSql();

        //本月详细
        $result['detail']['thisMonth'] = (new SqlSelect($conn,
            array('SUM(amount) AS amount, DATEDIFF(CURDATE(), date) AS daycount'), $db_name . '.Order',
            array(get_predicate_by_day_count(get_day_count(3))),
            ' GROUP BY daycount ORDER BY daycount')
        )->excecuteSql();

        //上月详情
        $result['detail']['lastMonth'] = (new SqlSelect($conn,
            array('SUM(amount) AS amount, DATEDIFF(CURDATE(), date) AS daycount'), $db_name . '.Order',
            array(get_predicate_by_day_count((int)$end_date->format('j'), $end_date->format('Y-m-d'))),
            ' GROUP BY daycount ORDER BY daycount')
        )->excecuteSql();

        //本周详情
        $result['detail']['thisWeek'] = (new SqlSelect($conn,
            array('SUM(amount) AS amount, DATEDIFF(CURDATE(), date) AS daycount'), $db_name . '.Order',
            array(get_predicate_by_day_count(get_day_count(2))),
            ' GROUP BY daycount ORDER BY daycount')
        )->excecuteSql();

        //上周详情
        $last_week_end_date = date_sub(date_create(),
            new DateInterval(sprintf('P%dD', get_day_count(2))));  // 上周最后一天
        $result['detail']['lastWeek'] = (new SqlSelect($conn,
            array('SUM(amount) AS amount, DATEDIFF(CURDATE(), date) AS daycount'), $db_name . '.Order',
            array(get_predicate_by_day_count(
                (int)$last_week_end_date->format('N'), $last_week_end_date->format('Y-m-d'))),
            ' GROUP BY daycount ORDER BY daycount')
        )->excecuteSql();

        //最受欢迎的菜品
        $result['mostPopularDishes'] = (new SqlSelect($conn,
            array('dishname', 'SUM(amount) as amount'),
            'DishLog',
            array('timestamp BETWEEN DATE_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY) AND CURRENT_TIMESTAMP()'),
            ' GROUP BY dishname ORDER BY amount DESC limit 6'))->excecuteSql();

        echo json_encode($result);
        break;

    //using parameter: tablenr, seat
    case 'getCurrentRound':
        $table_nr = $_GET['tablenr'];
        $seat = $_GET['seat'];
        echo (new SqlSelect($conn, array('currentRound'), 'Round',
            array(sprintf("tablenr='%04d'", $table_nr),
                sprintf('seat=%d', $seat))))->excecuteSql()[0]['currentRound'];

        break;

    case 'getCurrentPrice'://jxy当前价格
        $p = $_GET['p'];
        $sql_select = new SqlSelect($conn, array($p), 'dishes',
            array(sprintf("type='%s'", "Buffet"),"(children='no' or children='yes')"),' ORDER BY children asc');
        echo json_encode($sql_select->excecuteSql());
        break;

    //using parameter: tablenr, seat
    case 'getBuffetTime':
        $table_nr = $_GET['tablenr'];
        $seat = $_GET['seat'];

        $table_nr_str = sprintf("Table_%04d", $table_nr);

        echo (new SqlSelect($conn, ['timestamp'], $table_nr_str,
            ["seat='$seat'", "dishname='Buffet'"]))
            ->excecuteSql()[0]["timestamp"];
        break;

    //using parameter: name, seatCount, grouping
    case 'createTableWithName':
        // define a function to create table_tablenr with tablenr
        $create_table = function (mysqli $conn, $table_nr) {
            $columns = array("id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY",
                "dishname VARCHAR(45) NOT NULL",
                "dishId VARCHAR(20) NOT NULL",
                "price DECIMAL(10,2) NOT NULL",
                "amount DECIMAL(10,2) NOT NULL",
                "sended TINYINT(2) NOT NULL",
                "seat INT(10) NOT NULL",
                "children VARCHAR(10) NOT NULL",
                "orderId VARCHAR(45) NOT NULL",
                "timestamp TIMESTAMP",
                "addtime VARCHAR(13) NOT NULL"
            );
            $sql = sprintf("CREATE TABLE Table_%04d(%s) ", $table_nr, join(", ", $columns));
            $sql = $sql." ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_unicode_ci;";
            return $conn->query($sql);
        };

        //define a function to find the last tablenr
        $find_last_tablenr = function (mysqli $conn) {
            $sql_select = new SqlSelect($conn,
                array("MAX(tablenr)"),
                'TableIndex');
            $result = $sql_select->excecuteSql();

            return $result[0]['MAX(tablenr)'] + 1;
        };

        //define a function to register into TableIndex
        $register = function (mysqli $conn, $table_name, $table_nr, $seat_count, $grouping,$tableType) {
            $sql_insert = new SqlInsert($conn,
                'TableIndex',
                array('tablename', 'tablenr', 'seatCount', 'grouping', 'tableType'),
                array(sprintf("'%s'", $table_name),
                    sprintf("'%04d'", $table_nr),
                    $seat_count,
                    sprintf("'%s'", $grouping),
                    $tableType
                    ));
            return $sql_insert->excecuteSql();
        };

        //creat table
        $table_nr = $find_last_tablenr($conn);
        $result = $create_table($conn, $table_nr);
        if ($result !== true) {
            echo "Error on: " . "creating table" . "<br>" . $conn->error . "<br>";
        }

        //register into TableIndex
        $result = $register($conn, $_POST['name'], $table_nr, $_POST['seatCount'], $_POST['grouping'], $_POST['tableType']);
        if ($result === true) {
            if($_POST['tableType'] == '1'){
                echo "good<br><a  style='background:black;color:white;font-size: 30px' href='../html/Server/basic_table.html'>返回</a>";
            }else{
                echo "good<br><a  style='background:black;color:white;font-size: 30px' href='../html/Server/basic_table2.html'>返回</a>";
            }
            
        } else {
            echo "Error on: " . "registering into TableIndex" . "<br>" . $conn->error . "<br>";
        }
        break;

    //using parameter: tablenr
    case 'dropTableWithTablenr':
        $table_nr = (int)$_POST['tablenr'];

        $sql = sprintf("DROP TABLE Table_%04d", $table_nr);
        $result = $conn->query($sql);

        if ($result !== true) {
            echo "Error on: " . $sql . "<br>" . $conn->error . "<br>";
        }

        $sql_delete = new SqlDelete($conn, 'TableIndex', array(sprintf("tablenr='%04d'", $table_nr)));
        $result = $result && $sql_delete->excecuteSql();

        if ($result === true) {
            echo 'good';
        } else {
            echo "Error on: " . $sql_delete->get_sql() . "<br>" . $conn->error . "<br>";
        }
        break;

    //using parameter: orderInfo(Json)
    case 'addDishIntoCertainTable':
        $order_info = json_decode($_POST['orderInfo'], true);
        $table_nr = sprintf('%04d', (int)$order_info['tableID']);
        $table_name = $order_info['tableName'];
        $seat = $order_info['seat'];
        $children = $_POST['children'];
        $timestamp = $_POST['timestamp'];

        //是否重复提交
        $re = (new SqlSelect($conn, array('addtime'), sprintf("table_%s", $table_nr), array(sprintf("addtime='%s'", $timestamp))))->excecuteSql();
        if(count($re)==0){
            // 设置桌子已被占用
            $sql_update = (new SqlUpdate($conn, 'TableIndex', array('isUsing' => 1),array(sprintf("tablenr=%s", $table_nr))))->excecuteSql();
            //当前桌子座位计价方式
            $table_buffet_info = (new SqlSelect($conn, array('children','orderId'), sprintf("table_%s", $table_nr), array("dishname='Buffet'" ,sprintf("seat=%d", $seat))))->excecuteSql();
            $children = $table_buffet_info[0]['children'];
            $orderId = $table_buffet_info[0]['orderId'];

            foreach ($order_info['info'] as $dish) {
                $price = $dish['price'];
                if(!($children == "single" || $children == "takeout" || $dish['type2']=="Water" || $dish['type']=="Buffer" )){
                    $price = 0;
                }
                //插入到table
                $sql_insert = new SqlInsert($conn,
                    sprintf('Table_%s', $table_nr),
                    array('dishname',
                        'dishId',
                        'amount',
                        'sended',
                        'seat',
                        'children',
                        'price',
                        'orderId',
                        'addtime',
                    ),
                    array(
                        sprintf("'%s'", $dish['name']),
                        sprintf("'%s'", $dish['dishId']),
                        $dish['amount'],
                        0,
                        $seat,
                        sprintf("'%s'", $children),
                        $price,
                        sprintf("'%s'", $orderId),
                        sprintf("'%s'", $timestamp)
                    )
                );
                $result = $sql_insert->excecuteSql();
                if ($result !== true) {
                    echo "Error on: " . $sql_insert->get_sql() . "<br>" . $conn->error . "<br>";
                }
                $ptype = 1;
                if($children == "takeout"){
                    $ptype = 2;
                }
                $reception_kitchen = 2;//厨房
                if($children == "no" || $dish['type2']=="Water"){//自助餐和酒水
                    $reception_kitchen = 1; //前台
                }
                //插入到打印队列
                $sql_insert1 = new SqlInsert($conn,'printline_food',
                    array(
                        'tablename',
                        'seat',
                        'name',
                        'Chinesename',
                        'amount',
                        'isprint',
                        'ptype',
                        'reception_kitchen',
                    ),
                    array(
                        sprintf("'%s'", $table_name),
                        $seat,
                        sprintf("'%s'", $dish['name']),
                        sprintf("'%s'", $dish['Chinesename']),
                        $dish['amount'],
                        0, //0未打印 1已打印
                        $ptype,// 1 堂食 2外卖
                        $reception_kitchen,//1 前台 2厨房
                    )
                );
                $result1 = $sql_insert1->excecuteSql();
                if ($result1 !== true) {
                    echo "Error on: " . $sql_insert1->get_sql() . "<br>" . $conn->error . "<br>";
                }
            }

            echo 'good';
        }else{
            //重复提交
            echo 'repeat submit!';
        }
        break;

    case 'addDishIntoCertainTable2'://旧外卖
        $order_info = json_decode($_POST['orderInfo'], true);
        //订单id
        $get_order_id_prefix = function (mysqli $conn) {
            $sql_select = new SqlSelect($conn, array('restaurantId'), 'Info');
            return $sql_select->excecuteSql()[0]['restaurantId'] . date('Ymd');
        };
        $get_new_order_id_ending = function (mysqli $conn, $order_id_prefix) {
            global $db_name;
            $sql_select = new SqlSelect($conn, array("*"), $db_name . '.Order',
                array("id=(SELECT MAX(id) FROM " . $db_name . ".Order)"));
            $result = $sql_select->excecuteSql();
            //$old_prefix = substr($result[0]['orderId'], 0, 22);
            if(count($result)>0){
                $old_ending = (int)substr($result[0]['orderId'], 22);
                return ($old_ending + 1);
            }else{
                return 1;
            }
            
        };
        $order_id_prefix = $get_order_id_prefix($conn);
        $new_order_id = $order_id_prefix . $get_new_order_id_ending($conn, $order_id_prefix);

        //添加到log
        $t_price = 0.0;
        foreach ($order_info['info'] as $dish_to_log) {
            $sql_insert = (new SqlInsert($conn, 'DishLog',
                array('orderId','dishname', 'dishId', 'amount','price',  'seat'),
                array(sprintf("'%s'", $new_order_id),//订单id
                    sprintf("'%s'", $dish_to_log['name']),
                    sprintf("'%s'", $dish_to_log['dishId']),
                    $dish_to_log['amount'],
                    $dish_to_log['price'],
                    1)
                )
            );
            $result = $sql_insert->excecuteSql();
            if ($result !== true) {
                echo "Error on: " . $sql_insert->get_sql() . "<br>" . $conn->error . "<br>";
            }
            $t_price = $t_price + (int)$dish_to_log['amount'] * (float)$dish_to_log['price'];
        }

        //添加订单
        $sql_insert = new SqlInsert($conn, $db_name . '.Order',
            array('orderId',
                'date',
                'amount',
                'tablenr',
                'remark',
                'status'
            ),
            array(sprintf("'%s'", $new_order_id),
                "CURDATE()",
                $t_price,
                "'0000'",
                "'外卖'",
                "2"
            )
        );
        $result = $sql_insert->excecuteSql();
        if ($result !== true) {
                echo "Error on: " . $sql_insert->get_sql() . "<br>" . $conn->error . "<br>";
        }

        echo 'good';
        break;

    //using parameter: name, price, type, discribe
    case 'addDish':
        $get_latest_dish_id = function (mysqli $conn) {
            $sql_select = new SqlSelect($conn, array("dishId"), 'Dishes');
            $result = $sql_select->excecuteSql();
            return array_reduce($result, function ($carry, $item) {
                $temp = (int)substr($item['dishId'], -4);
                if ($carry < $temp) {
                    return $temp;
                } else {
                    return $carry;
                }
            }, 0);
        };

        $get_restaurant_info = function (mysqli $conn) {
            $sql_select = new SqlSelect($conn, array('*'), 'Info');
            return $sql_select->excecuteSql();
        };

        $id = $get_latest_dish_id($conn) + 1;
        // echo $id;
        if ($_FILES["file"]["error"] > 0) {
            //echo "Return Code: " . $_FILES["file"]["error"] . "<br />";//jxy
            echo "请添加一张图片<br /><br><a  style='background:black;color:white;font-size: 30px' href='javascript:history.back(-1);'>返回</a>";
            return;
        } else {
            $fileName = "../resource/image/dishImages/" . time() . ".jpg";

            if (file_exists($fileName)) {
                echo $fileName . " already exists. ";
                // return;
            } else {
                move_uploaded_file($_FILES["file"]["tmp_name"], $fileName);
            }
        }
        echo "添加成功，图片保存在: " . $fileName . "<br><a  style='background:black;color:white;font-size: 30px' href='../html/Server/dish.html'>返回</a>";
        //echo "添加成功，图片保存在: " . $fileName . "<br><a  style='background:black;color:white;font-size: 30px' href='../html/Server/html/dishAdd.html'>返回</a>";//jxy

        $price567 = $_POST['price'];
        if($_POST['type'] == 'Buffet'){
            $price567 = $_POST['price567'];
        }

        $sql_insert = new SqlInsert($conn,
            'Dishes',
            array('dishId', 'name','Chinesename', 'price', 'type','type2', 'discribe', 'imagename'),
            array(sprintf("'%s%04d'", $get_restaurant_info($conn)[0]['restaurantId'], $id),
                sprintf("'%s'", $_POST['name']),
                sprintf("'%s'", $_POST['Chinesename']),
                $_POST['price'],
                sprintf("'%s'", $_POST['type']),
                sprintf("'%s'", $_POST['type2']),
                sprintf("'%s'", $_POST['discribe']),
                sprintf("'%s'", $fileName)));
        $sql_insert->excecuteSql();

        break;

    //using parameter: tablenr(4 digits string), paymentId, [currency='EUR']
    case 'addOrder':  // 结账
        $currency = $_POST['currency'] ?? 'EUR';
        $table_nr = $_POST['tablenr'];
        $payment_id = $_POST['paymentId'];
        $tableName = $_POST['tableName'];
        
        if (($table_nr === '') || ($payment_id === '')) {
            break;
        }
        //总金额
        $get_total_amount = function (mysqli $conn, $tablenr) {
            $table = sprintf("Table_%04d", (int)$tablenr);
            $sql_select = new SqlSelect($conn, array("SUM(price*amount) as t_amount ,orderId,children"),$table);
            //echo $sql_select->get_sql();
            $result = $sql_select->excecuteSql();
            return $result[0];
        };
        $total_amount = $get_total_amount($conn, $table_nr);
        $total_price = $total_amount['t_amount'];
        $children = $total_amount['children'];
        //更新订单信息
        $sql_update = new SqlUpdate($conn, $db_name . '.Order',
            array('amount' =>$total_price,
                'paymentmethod' =>sprintf("'%s'", $payment_id),
                'currency'=>sprintf("'%s'", $currency),
                'remark' => "'已付账'",
                'status' => "1"),
            array(sprintf("orderId=%s", sprintf("'%s'", $total_amount['orderId'])))
            );
        $result = $sql_update->excecuteSql();
        //添加到打印队列
        $pre_tax = $total_price / 1.19;//税前
        $tax = $total_price / 1.19 * 0.19;//税
        if($children == "takeout"){
            $pre_tax = $total_price / 1.07;
            $tax = $total_price / 1.07 * 0.07;
        }

        $sql_insert1 = new SqlInsert($conn,'printline_order',
            array(
                'tablename',
                'orderId',
                'amount',
                'pre_tax',
                'tax',
                'isprint',
            ),
            array(
                sprintf("'%s'", $tableName),
                sprintf("'%s'", $total_amount['orderId']),
                $total_price,
                $pre_tax,
                $tax,
                0, //0未打印 1已打印
            )
        );
        $result1 = $sql_insert1->excecuteSql();
        if ($result1 !== true) {
            echo "Error on: " . $sql_insert1->get_sql() . "<br>" . $conn->error . "<br>";
        }


        /*
        // 结账时给水吧发账单
        $restaurant_info = (new SqlSelect($conn, array('*'), 'Info'))->excecuteSql()[0];
        $dish_detail = (new SqlSelect($conn, array('dishname', 'SUM(amount) as amount', $table_nr_str.'.price', 'type', 'Dishes.dishId'),
            sprintf('%s, Dishes', $table_nr_str),
            array(
                sprintf('%s.dishId=Dishes.dishId', $table_nr_str),
                sprintf("(type IN (%s))", join(', ', array_map(function ($item) {  // 无视普通菜品
                    return sprintf("'%s'", $item);
                }, $WATER)))),
            ' GROUP BY dishId'
        ));
        //echo $dish_detail->get_sql();
        $dish_detail->excecuteSql();
        $mail_messages['header'] = join(PHP_EOL, array(
            '\b' . $restaurant_info['name'],
            $restaurant_info['address'],
            "{$restaurant_info['postcode']} {$restaurant_info['city']}",
            $restaurant_info['tel'],
            str_repeat('*', $MAIL_LINE_LENGTH),
            ((new DateTime())->setTimezone(new DateTimeZone('Europe/Berlin')))
                ->format('Y-n-j H:i'),
            (new SqlSelect($conn, array('tablename'),
                'TableIndex', array(sprintf('tablenr=%04d', $table_nr))))->excecuteSql()[0]['tablename'],
            $new_order_id,  // 账单号
            str_repeat('-', $MAIL_LINE_LENGTH)));

        $mail_messages['footer'] = join(PHP_EOL, array(
            str_repeat('-', $MAIL_LINE_LENGTH),
            //sprintf("netto: €%.2f", $total_amount *0.81),//jxy//jxy
            //sprintf("mit 19%% Ust.: €%.2f", $total_amount * 0.19),//jxy
            sprintf("netto: €%.2f", $total_amount /1.19),//jxy
            sprintf("mit 19%% Ust.: €%.2f", $total_amount /1.19* 0.19),//jxy

            "Summe:",
            sprintf("\\b €%.2f", $total_amount),
            "UmsatzsteuerID {$restaurant_info['texnumber']}",
            str_repeat('*', $MAIL_LINE_LENGTH),
            'Aufwiedersehen!'));


        
        $mail_messages['body'] = array_map(function ($item) {
            global $MAIL_LINE_LENGTH;
            $local_sum_price = $item['amount'] * $item['price'];
            $result = array(wordwrap(sprintf('%s x %d', $item['dishname'], $item['amount']), $MAIL_LINE_LENGTH, PHP_EOL),
                sprintf("%'.40s", sprintf("€%.2f x %d = €%.2f", $item['price'], $item['amount'], $local_sum_price)));

            return join(PHP_EOL, $result);
        }, $dish_detail);

        $full_mail = join(PHP_EOL, array(
            $mail_messages['header'],
            join(PHP_EOL, $mail_messages['body']),
            $mail_messages['footer']));
        send_mail($WATER_BAR_MAIL_ADDRESS, 'billing', $full_mail);
        */

        $table_nr_str = sprintf('Table_%04d', $table_nr);
        // 记录菜品到dishLog
        $dishes_to_log = (new SqlSelect($conn,array('*'), $table_nr_str , null,' ORDER BY id asc '))->excecuteSql();

        foreach ($dishes_to_log as $dish_to_log) {
            (new SqlInsert($conn, 'DishLog',
                array('orderId','dishname', 'dishId', 'amount','price', 'children', 'seat'),
                array(sprintf("'%s'", $total_amount['orderId']),//订单id
                    sprintf("'%s'", $dish_to_log['dishname']),
                    sprintf("'%s'", $dish_to_log['dishId']),
                    $dish_to_log['amount'],
                    $dish_to_log['price'],
                    sprintf("'%s'", $dish_to_log['children']),
                    //sprintf("'%s'", $dish_to_log['type']),
                    $dish_to_log['seat'])
            ))->excecuteSql();
        }

        // 清空桌子
        $sql_delete = new SqlDelete($conn, sprintf("Table_%04d", (int)$table_nr), array("id>0"));
        $sql_delete->excecuteSql();

        // 设置桌子为可用
        $sql_update = (new SqlUpdate($conn, 'TableIndex',
            array('isUsing' => 0),
            array(sprintf("tablenr=%04d", $table_nr))))->excecuteSql();

        // 删除轮数信息
        (new SqlDelete($conn, 'Round', array(sprintf("tablenr=%04d", $table_nr))))->excecuteSql();

        if ($result === true) {
            echo 'good';
        } else {
            echo "Error on: " . $sql_update->get_sql() . "<br>" . $conn->error . "<br>";
        }

        break;

    //using parameter: typename, [countunit='']
    case 'addMenuInfo':
        if ($_POST['typename'] == "") {
            echo "need a type name." . "<br><a  style='background:black;color:white;font-size: 30px' href='../html/Server/html/menuTypeAdd.html'>返回</a>";
            return;
        }
        $sql_insert = new SqlInsert($conn, 'MenuInfo',
            array('typename',
                'countunit',
                'type2'),
            array(sprintf("'%s'", $_POST['typename']),
                sprintf("'%s'", $_POST['countunit']),
                sprintf("'%s'", $_POST['type2']),
            ));

        $sql_insert->excecuteSql();
        echo "添加成功<br><a  style='background:black;color:white;font-size: 30px' href='../html/Server/html/menuTypeAdd.html'>返回</a>";
        break;

    //修改菜品种类
    case 'updateMenuInfo':
        if ($_POST['typename'] == "") {
            echo "need a type name." . "<br><a  style='background:black;color:white;font-size: 30px' href='../html/Server/html/menuTypeAdd.html'>返回</a>";
            return;
        }

        $updateArr = array('typename' => sprintf("'%s'", $_POST['typename']),
                'countunit' => sprintf("'%s'", $_POST['countunit']),
                'type2' => sprintf("'%s'", $_POST['type2']),
                );

        
        $sql_update = new SqlUpdate($conn, 'MenuInfo',$updateArr,array(sprintf("id=%d", $_POST['id'])));
        $result = $sql_update->excecuteSql();

        if ($result === true) {
            echo "修改成功<br><a  style='background:black;color:white;font-size: 30px' href='../html/Server/html/menuTypeAdd.html'>返回</a>";
        } else {
            echo "Error on: " . $sql_update->get_sql() . "<br>" . $conn->error . "<br>";
        }

        break;

    //using parameter: tablenr, seat
    case 'addBuffetInTable':
        $table_nr = $_POST['tablenr'];
        $seat = $_POST['seat'];
        $children = $_POST['children'];
        $dateCount = (int)$_POST['dateCount'];

        
        $lock = new CacheLock('openSeat');
        $lock->lock();
        //检测是否重复
        $table_buffet_info = (new SqlSelect($conn, array('children'), sprintf("table_%s", $table_nr), array("dishname='Buffet'" ,sprintf("seat=%d", $seat))))->excecuteSql();
        if(count($table_buffet_info)>0){
            echo $table_buffet_info[0]['children'];
        }else{
            // 设置桌子已被占用
            (new SqlUpdate($conn, 'TableIndex',
                array('isUsing' => 1),
                array(sprintf("tablenr=%s", $table_nr))))->excecuteSql();

            // 在轮数表里加入桌子和座位信息
            (new SqlInsert($conn, 'Round',
                array('tablenr', 'seat', 'currentRound'),
                array(sprintf("'%04d'", $table_nr), $seat, 0)))->excecuteSql();

            

            $new_order_id = '-1';
            //检测订单是否重复,查询table_xxx表
            $table_buffet_info = (new SqlSelect($conn, array('orderId'), sprintf("table_%s", $table_nr), array("dishname='Buffet'" )))->excecuteSql();
            if(count($table_buffet_info) > 0){
                $new_order_id = $table_buffet_info[0]['orderId'];
            }else{
                //添加订单
                $get_order_id_prefix = function (mysqli $conn) {
                    //$sql_select = new SqlSelect($conn, array('restaurantId'), 'Info');
                    //return $sql_select->excecuteSql()[0]['restaurantId'] . date('Ymd');
                    return "DE" . date('Y');
                };

                $get_new_order_id_ending = function (mysqli $conn, $order_id_prefix) {
                    global $db_name;
                    $sql_select = new SqlSelect($conn, array("*"), $db_name . '.Order',
                        array("1 = 1"),"and orderId like '".$order_id_prefix."%'order by id desc limit 1");
                    $result = $sql_select->excecuteSql();
                    if(count($result)>0){
                        $old_ending = (int)substr($result[0]['orderId'], 6);
                        return ($old_ending + 1);
                    }else{
                        return 1;
                    }
                    
                };
                $order_id_prefix = $get_order_id_prefix($conn);
                $new_order_id = $order_id_prefix . sprintf("%010d", $get_new_order_id_ending($conn, $order_id_prefix));
                //桌子区域
                $tablearea = new SqlSelect($conn, array('grouping'), 'tableindex',array(sprintf("tablenr='%s'",  $table_nr)));
                $sql_insert = new SqlInsert($conn, $db_name . '.Order',
                    array('orderId',
                        'date',
                        'tablenr',
                        'remark',
                        'status',
                        'tablearea',
                    ),
                    array(sprintf("'%s'", $new_order_id),
                        "CURDATE()",
                        sprintf("'%s'",  $table_nr),
                        "'用餐中'",
                        "0",
                        sprintf("'%s'",  $tablearea->excecuteSql()[0]['grouping']),
                    )
                );
                $result = $sql_insert->excecuteSql();
                //echo $sql_insert->get_sql();
            }

            // 获取自助餐信息
            $buffet_info = (new SqlSelect($conn, array('*'), 'Dishes', array("type='Buffet'" ,sprintf("children='%s'", $children))))->excecuteSql()[0];
            //根据节假日 工作日不同价格
            $price = "price";
            //当前hour
            $hour = (int)date("H");
            if($dateCount > 0 ){//节假日
                if($hour < 17){ //0-16
                    $price = "price567";
                }else{//17-23
                    $price = "price567_pm";
                }
            }else{//非节假日
                if($hour < 17){ //0-16
                    $price = "price";
                }else{//17-23
                    $price = "price_pm";
                }
            }

            // 给桌子加入自助餐
            $sql_insert = new SqlInsert($conn,
                sprintf('Table_%s', $table_nr),
                array('dishname',
                    'dishId',
                    'amount',
                    'sended',
                    'seat',
                    'children',
                    'price',
                    'orderId',
                ),
                array(
                    sprintf("'%s'", $buffet_info['name']),
                    sprintf("'%s'", $buffet_info['dishId']),
                    1,
                    1,
                    $seat,
                    sprintf("'%s'", $children),
                    $buffet_info[$price],
                    sprintf("'%s'", $new_order_id)
                )
            );
            $result = $sql_insert->excecuteSql();
            if ($result !== true) {
                echo "Error on: " . $sql_insert->get_sql() . "<br>" . $conn->error . "<br>";
            } else {
                echo 'good';
            } 
        }
        $lock->unlock();
        break;
    case 'updateTable':
        $tableType = $_POST['tableType'];
        $updateArr = array('tablename' => sprintf("'%s'", $_POST['name']),
                'seatCount' =>$_POST['seatCount'],
                'grouping' => sprintf("'%s'", $_POST['grouping'])
                );

        
        $sql_update = new SqlUpdate($conn, 'TableIndex',$updateArr,array(sprintf("id=%d", $_POST['id'])));
        $result = $sql_update->excecuteSql();

        if ($result === true) {
            if($tableType == "2"){
                echo "修改成功<br><a  style='background:black;color:white;font-size: 30px' href='../html/Server/basic_table2.html'>返回</a>";
            }else{
                echo "修改成功<br><a  style='background:black;color:white;font-size: 30px' href='../html/Server/basic_table.html'>返回</a>";
            }
        } else {
            echo "Error on: " . $sql_update->get_sql() . "<br>" . $conn->error . "<br>";
        }
        break;
    //using parameter: dishId, name, price, type, discribe
    case 'updateDish':
        $timestr = time();

        $updateArr = array('name' => sprintf("'%s'", $_POST['name']),
                'Chinesename' => sprintf("'%s'", $_POST['Chinesename']),
                'price' =>  $_POST['price'],
                'type' => sprintf("'%s'", $_POST['type']),
                'type2' => sprintf("'%s'", $_POST['type2']),
                'discribe' => sprintf("'%s'", $_POST['discribe'])
                );

        if ($_FILES["file"]["error"] > 0) {
            
        } else {
            $fileName = "../resource/image/dishImages/" .$timestr. ".jpg";

            if (file_exists($fileName)) {
                echo $fileName . " already exists. ";
                // return;
            } else {
                move_uploaded_file($_FILES["file"]["tmp_name"], $fileName);
            }

            $updateArr['imagename'] = sprintf("'../resource/image/dishImages/%s.jpg'", $timestr);
        }
        
        $sql_update = new SqlUpdate($conn, 'Dishes',$updateArr,array(sprintf("id=%d", $_POST['id'])));
        $result = $sql_update->excecuteSql();

        if ($result === true) {
            echo "修改成功<br><a  style='background:black;color:white;font-size: 30px' href='../html/Server/dish.html'>返回</a>";
        } else {
            echo "Error on: " . $sql_update->get_sql() . "<br>" . $conn->error . "<br>";
        }
        break;

    case 'updateBuffet':
        $timestr = time();
        $updateArr = array('name' => sprintf("'%s'", $_POST['name']),
                'Chinesename' => sprintf("'%s'", $_POST['Chinesename']),
                'price' =>  $_POST['price'],
                'price567' => $_POST['price567'],
                'price_pm' =>  $_POST['price_pm'],
                'price567_pm' => $_POST['price567_pm'],
                'discribe' => sprintf("'%s'", $_POST['discribe'])
                );

        if ($_FILES["file"]["error"] > 0) {
            
        } else {
            $fileName = "../resource/image/dishImages/" .$timestr. ".jpg";

            if (file_exists($fileName)) {
                echo $fileName . " already exists. ";
                // return;
            } else {
                move_uploaded_file($_FILES["file"]["tmp_name"], $fileName);
            }

            $updateArr['imagename'] = sprintf("'../resource/image/dishImages/%s.jpg'", $timestr);
        }
        
        $sql_update = new SqlUpdate($conn, 'Dishes',$updateArr,array(sprintf("id=%d", $_POST['id'])));
        $result = $sql_update->excecuteSql();

        if ($result === true) {
            echo "修改成功<br><a  style='background:black;color:white;font-size: 30px' href='../html/Server/buffet.html'>返回</a>";
        } else {
            echo "Error on: " . $sql_update->get_sql() . "<br>" . $conn->error . "<br>";
        }
        break;

    //using parameter: roundlength, roundcount, unitprice
    case 'updateJapanBuffetInfo':
        $round_length = $_POST['roundlength'];
        $round_count = $_POST['roundcount'];
        $unit_price = $_POST['unitprice'];
        $sql_update = (new SqlUpdate($conn, 'JapanBuffetInfo',
            array('roundLength' => $round_length,
                'roundCount' => $round_count,
                'unitPrice' => $unit_price),
            array('id=(SELECT MAX(id) FROM JapanBuffetInfo)')));
        $result = $sql_update->excecuteSql();
        if ($result === true) {
            echo 'good';
        } else {
            echo "Error on: " . $sql_update->get_sql() . "<br>" . $conn->error . "<br>";
        }
        break;

    //using parameter: tablenr, seat
    case 'updateCurrentRound':
        $table_nr = $_POST['tablenr'];
        $seat = $_POST['seat'];
        $sql_update = (new SqlUpdate($conn, 'Round',
            array('currentRound' => 'currentRound+1'),
            array(sprintf('tablenr=%04d', $table_nr),
                sprintf('seat=%d', $seat))));

        $result = $sql_update->excecuteSql();
        if ($result !== true) {
            echo "Error on: " . $sql_update->get_sql() . "<br>" . $conn->error . "<br>";
        } else {
            echo 'good';
        }
        break;

    //using parameter: dishId
    case 'deleteDish':
        $dish_id = $_POST['dishId'];
        $dish_image_filename = get_dish_detail_by_id($conn, $dish_id)[0]['imagename'];
        $result = unlink($dish_image_filename);
        if (!$result) {
            echo 'Error on unlinking image file';
        }

        $sql_delete = new SqlDelete($conn, 'Dishes', array(sprintf("id=%s", $_POST['dishId'])));
        $result = $sql_delete->excecuteSql();
        if ($result === true) {
            echo 'good';
        } else {
            echo "Error on: " . $sql_delete->get_sql() . "<br>" . $conn->error . "<br>";
        }
        break;

    //using parameter: typename
    case 'deleteMenuInfo':
        $sql_delete = new SqlDelete($conn, 'MenuInfo', array(sprintf("typename='%s'", $_POST['typename'])));
        $result = $sql_delete->excecuteSql();
        if ($result === true) {
            echo 'good';
        } else {
            echo "Error on: " . $sql_delete->get_sql() . "<br>" . $conn->error . "<br>";
        }
        break;

    //using parameter: email, password
    case 'authorizeLogin':
        $email = $_GET['email'];
        $password = $_GET['password'];

        $allow_login = (new SqlSelect($conn, array('COUNT(*)'), 'Person',
            array(sprintf("(email='%s')", $email),
                sprintf("(loginPassword='%s')", $password)))
        )->excecuteSql()[0]['COUNT(*)'];

        if ($allow_login) {
            echo 'good';
        } else {

            $user_exists = (new SqlSelect($conn, array('COUNT(*)'), 'Person',
                array(sprintf("email='%s'", $email))))->excecuteSql()[0]['COUNT(*)'];
            if ($user_exists) {
                echo '密码错误';
            } else {
                echo '用户不存在';
            }
        }
        break;

    //using parameter: email
    case 'forgetPassword':
        $email = $_POST['email'];
        $string_start_index = rand(0, 23);
        $string_length = 8;
        $password_reset_expire = 30;  //分钟
        $random_string = substr(md5(time()), $string_start_index, $string_length);
        $mail_messages = array(
            '请先确认本次重置密码是否是您本人操作。',
            '',
            '然后您可以点击下面的链接来重置您的密码。',
            urlencode(
                sprintf('[此处应有链接]?hash=%s&email=%s', $random_string, $email)  // todo: 添加重置密码页面链接
            ),
            '',
            sprintf('本链接仅在%d分钟内生效，请尽快操作。', $password_reset_expire),
            sprintf('服务器时间：%s', (new DateTime())->format('Y-m-d H:i:s P')),
        ); 

        // 在数据库中记录生成的随机密码
        (new SqlUpdate($conn, 'Person',
            array('forgetPassword' => $random_string,
                'passwordResetBefore' => sprintf("DATE_ADD(NOW(), INTERVAL %s MINUTE)", $password_reset_expire)),
            array(sprintf("email='%s'", $email))))->excecuteSql();

        // 发送邮件
        send_mail($email, '重置您的XStar密码', join(PHP_EOL, $mail_messages));
        break;

    //using parameter: email, hash
    case 'comfirmPassword':
        $email = $_POST['email'];
        $hash = $_POST['hash'];
        $confirm_password_reset = (new SqlSelect($conn, array('COUNT(*)'), 'Person',
            array(sprintf("(email='%s')", $email),
                sprintf("(forgetPassword='%s')", $hash),
                sprintf("(passwordResetBefore>NOW())")))
        )->excecuteSql()[0]['COUNT(*)'];

        if ($confirm_password_reset) {
            (new SqlUpdate($conn, 'Person',
                array('loginPassword' => sprintf("'%s'", $hash),
                    'forgetPassword' => "''",
                    'passwordResetBefore' => "''"),
                array(sprintf("(email=%s)", $email))
            ))->excecuteSql();

            echo '您的新密码是：' . $hash;
        } else {
            echo '重置密码操作已过期，请重新申请重置';
        }
        break;

    //using parameter: tablenr
    case 'callService':
        $tableName = $_POST['tableName'];
        $seat = $_POST['seat'];
        $sql_insert1 = new SqlInsert($conn,'printline_service',
            array(
                'tablename',
                'seat'
            ),
            array(
                sprintf("'%s'", $tableName),
                sprintf("'%s'", $seat)
            )
        );
        $result1 = $sql_insert1->excecuteSql();
        if ($result1 !== true) {
            echo "Error on: " . $sql_insert1->get_sql() . "<br>" . $conn->error . "<br>";
        }
        break;

    //using parameter:
    case 'sendOrder':
        // 从TableIndex里选择所有已经占用的桌子
        $table_nrs = (new SqlSelect($conn, array('tablenr', 'tablename'), 'TableIndex', array('(isUsing<>0)')))->excecuteSql();
        $mail_messages = array();

        $mail_messages['footer'] = join(PHP_EOL, array(
            str_repeat('-', $MAIL_LINE_LENGTH),
            sprintf('Datum：%s', ((new DateTime())->setTimezone(new DateTimeZone('Europe/Berlin')))
                ->format('Y-n-j H:i')),
            str_repeat('*', $MAIL_LINE_LENGTH)));

        // 每个桌子执行
        foreach ($table_nrs as $table_nr) {
            $mail_messages['header'] = join(PHP_EOL, array(
                str_repeat('*', $MAIL_LINE_LENGTH),
                $table_nr['tablename'],
                str_repeat('-', $MAIL_LINE_LENGTH)));

            $table = sprintf('Table_%s', $table_nr['tablenr']);

            $dishes_to_kitchen = (new SqlSelect($conn, array($table . '.dishID', 'dishname', 'SUM(amount)', 'type'),
                sprintf('%s, Dishes', $table),
                array('(sended=0)',
                    sprintf('(%s.dishId=Dishes.dishId)', $table),
                    "(type NOT IN ('Wein', 'Eis & Kaffee', 'Getränke'))"
                ), ' GROUP BY dishname'))->excecuteSql();

            $dishes_to_waterbar = (new SqlSelect($conn, array($table . '.dishID', 'dishname', 'SUM(amount)', 'type'),
                sprintf('%s, Dishes', $table),
                array('(sended=0)',
                    sprintf('(%s.dishId=Dishes.dishId)', $table),
                    "(type IN ('Wein', 'Eis & Kaffee', 'Getränke'))"
                ), ' GROUP BY dishname'))->excecuteSql();

            // 分别给厨房和水吧发邮件
//            if (!empty($dishes_to_kitchen)) {
//                send_mail($KITCHEN_MAIL_ADDRESS, 'toKitchen', join(PHP_EOL, array(
//                    $mail_messages['header'],
//                    join(PHP_EOL, array_map(function ($item) {
//                        global $MAIL_LINE_LENGTH;
//                        return wordwrap(sprintf('%sx%d', $item['dishname'], $item['SUM(amount)']),
//                            $MAIL_LINE_LENGTH, PHP_EOL);
//                    }, $dishes_to_kitchen)),
//                    $mail_messages['footer'])));
//            }
//            if (!empty($dishes_to_waterbar)) {
//                send_mail($WATER_BAR_MAIL_ADDRESS, 'toWaterBar', join(PHP_EOL, array(
//                    $mail_messages['header'],
//                    join(PHP_EOL, array_map(function ($item) {
//                        global $MAIL_LINE_LENGTH;
//                        return wordwrap(sprintf('%sx%d', $item['dishname'], $item['SUM(amount)']),
//                            $MAIL_LINE_LENGTH, PHP_EOL);
//                    }, $dishes_to_waterbar)),
//                    $mail_messages['footer'])));
//            }
            foreach ($dishes_to_kitchen as $dish_to_kitchen) {
                send_mail($KITCHEN_MAIL_ADDRESS, 'toKitchen', join(PHP_EOL, array(
                    $mail_messages['header'],
                    wordwrap(sprintf('%sx%d', $dish_to_kitchen['dishname'], $dish_to_kitchen['SUM(amount)']),
                        $MAIL_LINE_LENGTH, PHP_EOL),
                    $mail_messages['footer'])));
            }
            foreach ($dishes_to_waterbar as $dish_to_waterbar) {
                send_mail($WATER_BAR_MAIL_ADDRESS, 'toWaterbar', join(PHP_EOL, array(
                    $mail_messages['header'],
                    wordwrap(sprintf('%sx%d', $dish_to_waterbar['dishname'], $dish_to_waterbar['SUM(amount)']),
                        $MAIL_LINE_LENGTH, PHP_EOL),
                    $mail_messages['footer'])));
            }

            // 把桌子里的sended都改成1
            (new SqlUpdate($conn, $table, array('sended' => '1'), array('sended=0')))->excecuteSql();
        }
        echo 'good';
        break;

    default:
        echo 'no such method';
}