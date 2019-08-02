<?php
header('Content-type: application/json');
header("Access-Control-Allow-Origin: *");
$response = array(
    'code' => 0,
    'message' =>'all Green',
    'data' => array(
        array(
            'name'=>'reis',
            'img'=>'/Beilage/白饭.jpg',
            'discibe'=>'weißer gedünsteter reis',
            'type'=>'beilag',
        ),
        array(
            'name'=>'gebr, nudeln',
            'img'=>'/Beilage/炒面.jpg',
            'discibe'=>'gebratene nudeln mit zwiebein, und kohl.',
            'type'=>'beilag',
        ),
        array(
            'name'=>'gemüse',
            'img'=>'/Beilage/蔬菜.jpg',
            'discibe'=>'eine gesunde medley aus brokkoli, zucchini, karotten, bohnen und kohl.',
            'type'=>'beilag',
        ),
        array(
            'name'=>'gebr, reis',
            'img'=>'/Beilage/炒饭.jpg',
            'discibe'=>'zubereitete gedünstete weiße reis mit sojasauce, eier, erbsen, karotten.',
            'type'=>'beilag',
        ),
        array(
            'name'=>'beijing beef',
            'img'=>'/hauptGericht/洋葱niu.jpg',
            'discibe'=>'knusprige mariniertes rindfleisch, mit zwiebeln, rote paprika und einem berühmte sauce.',
            'type'=>'hauptgericht',
        ),
        array(
            'name'=>'hongkong chicken',
            'img'=>'/hauptGericht/甜子鸡.jpg',
            'discibe'=>'unsere unterschrift gericht.
süße und würzige knuspriges huhn beißt unsere  pikanten-sauce.',
            'type'=>'hauptgericht',
        ),
        array(
            'name'=>'orange huhn würzig',
            'img'=>'/hauptGericht/橙子鸡.jpg',
            'discibe'=>'knuspriges hähnchen in einer süß-scharfen-würzige orangensauce.',
            'type'=>'hauptgericht',
        ),


        array(
            'name'=>'shanghai steaks',
            'img'=>'/hauptGericht/长豆牛1.jpg',
            'discibe'=>'steaks mit frische bohnen, zwiebeln und champignons in einer würzigen sauce.',
            'type'=>'hauptgericht',
        ),


        array(
            'name'=>'gong bao chicken',
            'img'=>'/hauptGericht/宫保鸡.jpg',
            'discibe'=>'ein sichuan-inspiriertes gericht mit huhn, und gemüse, verfeinert',
            'type'=>'hauptgericht',
        ),


        array(
            'name'=>'grüne bohnen-hänchenbrust',
            'img'=>'/hauptGericht/长豆鸡.jpg',
            'discibe'=>'hähnchenbrust,bohnen und zwiebeln in einer milden lngver-sojasauce würzen.',
            'type'=>'hauptgericht',
        ),


        array(
            'name'=>'hähnchen streifen',
            'img'=>'/hauptGericht/炸鸡条.jpg',
            'discibe'=>'knusprige-goldene hähnchen streifen.
mit eine ausgewählt soße.',
            'type'=>'hauptgericht',
        ),


        array(
            'name'=>'hähnchen brust',
            'img'=>'/hauptGericht/炸鸡胸1.jpg',
            'discibe'=>'gebratene-goldene hähnchenbrust, mit eine ausgewählt soße.',
            'type'=>'hauptgericht',
        ),


        array(
            'name'=>'champignons',
            'img'=>'/hauptGericht/毛菇.jpg',
            'discibe'=>'frische champignons knoblauch körner, mit austern-sauce.',
            'type'=>'hauptgericht',
        ),


        array(
            'name'=>'knusprige enten',
            'img'=>'/hauptGericht/炸鸭.jpg',
            'discibe'=>'knusprige ente, mit verschidene gemüse und eine ausgewählt soße.',
            'type'=>'hauptgericht',
        ),


        array(
            'name'=>'Glückskeks',
            'img'=>'/vorpeisen/幸运饼.jpg',
            'discibe'=>'süß-sauer-scharf mit paprika, champignons, bambus, hühnerfleisch, und eie.',
            'type'=>'vorspeisen',
        ),


        array(
            'name'=>'knusprige shrimps',
            'img'=>'/vorpeisen/炸大虾.jpg',
            'discibe'=>'crisp-golden butterflied garnelen.',
            'type'=>'vorspeisen',
        ),


        array(
            'name'=>'chickensrollen',
            'img'=>'/vorpeisen/肉卷.jpg',
            'discibe'=>'kohl, karotten pilze, zwiebeln und hühnerfleisch in einer knusprigen wan-tan-wrapper.',
            'type'=>'vorspeisen',
        ),


        array(
            'name'=>'frühlingspollen',
            'img'=>'/vorpeisen/蔬菜卷.jpg',
            'discibe'=>'kohl, sellerie, karotten, zwiebeln und chinesische nudeln in einem knusprigen wan-tan-wrapper.',
            'type'=>'vorspeisen',
        ),


        array(
            'name'=>'süß-sauer-soße',
            'img'=>'/sauce/甜酸汁.jpg',
            'discibe'=>'',
            'type'=>'sauce',
        ),


        array(
            'name'=>'erdnuss-soße',
            'img'=>'/sauce/花生汁.jpg',
            'discibe'=>'',
            'type'=>'sauce',
        ),


        array(
            'name'=>'knoblauch-soße',
            'img'=>'/sauce/黑汁.jpg',
            'discibe'=>'',
            'type'=>'sauce',
        ),


        array(
            'name'=>'curry-soße',
            'img'=>'/sauce/咖喱汁1.jpg',
            'discibe'=>'',
            'type'=>'sauce',
        ),


        array(
            'name'=>'scharf-soße',
            'img'=>'/sauce/辣汁.jpg',
            'discibe'=>'',
            'type'=>'sauce',
        ),


        array(
            'name'=>'orange-soße',
            'img'=>'/sauce/橙子.jpg',
            'discibe'=>'',
            'type'=>'sauce',
        ),
        array(
            'name'=>'BONAQA TABLEWATER',
            'img'=>'/getranke/BONAQATABLEWATER.jpg',
            'discibe'=>'',
            'type'=>'getranke',
        ),
        array(
            'name'=>'CocaCola Light',
            'img'=>'/getranke/CocaColalight.jpg',
            'discibe'=>'',
            'type'=>'getranke',
        ),      array(
            'name'=>'CocaCola Zero',
            'img'=>'/getranke/CocaColaZero.jpg',
            'discibe'=>'',
            'type'=>'getranke',
        ),      array(
            'name'=>'CocaCola',
            'img'=>'/getranke/CocaCola.jpg',
            'discibe'=>'',
            'type'=>'getranke',
        ),      array(
            'name'=>'Fanta',
            'img'=>'/getranke/Fanta.jpg',
            'discibe'=>'',
            'type'=>'getranke',
        ),      array(
            'name'=>'Lift APFERLSCHORLE',
            'img'=>'/getranke/LiftAPFERLSCHORLE.jpg',
            'discibe'=>'',
            'type'=>'getranke',
        ),      array(
            'name'=>'Sprite',
            'img'=>'/getranke/Sprite.jpg',
            'discibe'=>'',
            'type'=>'getranke',
        ),
        array(
            'name'=>'Vio STELL',
            'img'=>'/getranke/VioSTELL.jpg',
            'discibe'=>'',
            'type'=>'getranke',
        ),




    ),
);

echo json_encode($response, JSON_FORCE_OBJECT);



/**
 * Created by PhpStorm.
 * User: Juhaodong
 * Date: 2018/1/14
 * Time: 11:32
 */