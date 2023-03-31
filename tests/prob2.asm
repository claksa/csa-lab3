db 1 ;first number
db 2 ;second number
db 4000000
db 2 ;summary of even
db 2 ;const
loop:
    ld acc 0
    ld r7 1
    add acc r7
    sv acc 1
    sv r7 0
compare:
    ld br 2
    sub br acc
    jn test_odd
    jmp end
test_odd:
    ld r7 4
    mov acc br
    div r7 br
    test dr
    jz sum
    jmp loop
sum:
    ld br 3
    add br acc
    sv br 3
    jmp loop
end:
    ld acc 3
    halt


