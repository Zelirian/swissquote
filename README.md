# meine dokumentation
````puml
@startuml
    actor cartGui
    cartGui -> cartControl : test sensor (sensorId)\n<font color=red><b>mg.cartCommand.TEST_SENSOR
    cartControl -> cartArduino : test sensor\n<font color=red><b>7,<sensorId>
    loop 5 seconds
        cartArduino -> cartControl : sensor distances\n<font color=blue><b>!A7
        cartControl -> cartGui : measured distances
        cartGui -> cartGui : display values\ncalculate and display average
    end
@enduml
````


````puml
@startuml
:Main Admin: as Admin
(Use the application) as (Use)

User -> (Start)
User --> (Use)

Admin ---> (Use)

note right of Admin : This is an example.

note right of (Use)
A note can also
be on several lines
end note

note "This note is connected\nto several objects." as N2
(Start) .. N2
N2 .. (Use)
@enduml
````
