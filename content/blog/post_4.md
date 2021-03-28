---
categories:
- Data basic
-
date: "2021-03-28"
description: Two Column Vlookup function
draft: false
tags:
- Excel
- VBA

title: Two Criteria excel Vlookup
---

Two Criteria excel Vlookup function 
=======

Excel is a good tool and usually have all things needed already built in. For structuring data Pivot table are awesome. And also to find and draw new insights of data. However recently I found that sometimes when looking up data in a model you want to Vlookup on multiple criterias (one could usually use pivot tables but that add an extra step in the model). The common approach have been to merge the lookup columns into one (this to have an unique key to lookup from). This works fine but I see it as a more of a quick and dirty solution. Another approach could be to start using the function above. 

In excel press "Alt + F11" and create a new module and simple past the code below.
This will enable a two column vlookup which works similar to a regular Vlookup but with the possiblity to add an extra lookup criteria.


```js
Function Two_Col_Vlookup(Table_Range As Range, Col1_Fnd, Col2_Fnd, Return_Col As Long)


Dim rCheck As Range, bFound As Boolean, lLoop As Long


    On Error Resume Next

    Set rCheck = Table_Range.Columns(1).Cells(1, 1)

    With WorksheetFunction

        For lLoop = 1 To .CountIf(Table_Range.Columns(1), Col1_Fnd)

           Set rCheck = Table_Range.Columns(1).Find(Col1_Fnd, rCheck, xlValues, xlWhole, xlNext, xlRows, False)

           If UCase(rCheck(1, 2)) = UCase(Col2_Fnd) Then

                bFound = True

                Exit For

            End If

        Next lLoop

    End With



    If bFound = True Then

        Two_Con_Vlookup = rCheck(1, Return_Col)

    Else

     Two_Con_Vlookup = "N/A"

    End If
```


