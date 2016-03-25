<?php
include "config.php";

//Get name of table passed in
$table= $_GET['name'];

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

//Get first date to select data
$oldDate = $_GET['oldDate'];

//Get first date to select data
$curDate = $_GET['curDate'];

//Try connecting to database
try {
    $connection= new PDO('mysql:host='.$conHost.';dbname='.$database.';charset=utf8',$conUser,$conPass);
    if(!$connection){
        die('Not connected: ');
    }
} catch(PDOException $pdex) {
    echo "Error connecting to DB. " .$pdex->getMessage();
}

//Set the query to perform on the database. If order is present, use as specified.
if(isset($order)) {
    $query="Select * from " . $table . " order by RecNbr " . $order;
} elseif (isset($oldDate) && isset($curDate)) {
    $query="select * from " .$table . " where _datetime between " .$oldDate . " and " .$curDate;
} else {
    $query="select * from " . $table;
}
//Try performing query
$result=$connection->query($query) or die('Invalid query!');

//Hold headers
$headers = '';

//Get number of fields returned
$fields = $result->columnCount();

//Get csv headers and append to $header variable
for ( $i = 0; $i < $fields; $i++ )
{
    //Don't include comma on end field
    if($i+1 != $fields) {
        $header .= $result->getColumnMeta($i)['name'].",";
    } else {
        $header .= $result->getColumnMeta($i)['name'];
    }
}

//Holds data
$data = '';

//Iterate over result set and append data to return
while($row = $result->fetch(PDO::FETCH_ASSOC)) {
    $line = '';
    //Used to detect if this last field is reached
    $count = 0;
    //For every row returned, treat it as value
    foreach($row as $value)
    {                                            
        $count++;
        //Check if there was no value for specific data point, if so, skip
        if((!isset($value)) || ($value == ""))
        {
            $value = ",";
        }
        else
        {
            //Replace "'s in value with nothing, then append a comma
            $value = str_replace('"' , ' ', $value);
            //If not the last row, append a comma 
            if($count != $fields) {
                $value = $value.",";
            }
        }
        //Add to full line
        $line .= $value;
    }
    //Trim whitespace and append new line
    $data .= trim($line) . "\n";
}
//Close connection
$connection=null;

header("Content-Disposition: attachment; filename=".$table.".csv");
print "$header\n$data";
?>
