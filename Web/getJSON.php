<?php
include "config.php";

//Get name of table passed in
$table = $_GET['name'];

//Make sure table name is provided, then check if an allowed table was entered. Unfortunately,
//PDO does not allow prepared statements with column or table names...
if(!isset($table)) {
    echo("Invalid arguments provided");
    exit(1);
} else if (strcmp($table,"table15min") && strcmp($table, table24hr)) {
    echo("Invalid arguments provided");
    exit(2);
}
//Get sorting order for database
$order= $_GET['order'];

//Try connecting to database
$connection= new PDO('mysql:host='.$conHost.';dbname='.$database, $conUser, $conPass,
    array(PDO::ATTR_EMULATE_PREPARES => false));
if(!$connection){
    die('Not connected: ');
}
//Set so that all errors are treated as exceptions
$connection->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);

//Set the query to perform on the database. If order is present, use as specified.
if(isset($order)) {
    $query= $connection->prepare("select * from ".$table." order by RecNbr ".$order);
} else {
    $query= $connection->prepare("select * from $table");
}

try{
    //Try performing query
    if($rv = $query->execute()) {
        //Holds data
        $data = array();
        //Create/execute query to get column names
        $q = $connection->prepare("DESCRIBE ".$table);
        $q->execute();
        //Get columns from result
        $fields = $q->fetchAll(PDO::FETCH_COLUMN); 
        //Iterate over result set and append data to return
        $rtn = array();
        while($row = $query->fetch(PDO::FETCH_ASSOC)) {
            //Combine current row with fields previosuly given
            array_push($rtn,array_combine($fields,$row));
        }

        header("Content-Type:application/json");
        print json_encode($rtn);
    }  
} catch (PDOException $e) {
    //Print error
    echo "Error: " . $e->getMessage();
}
?>
