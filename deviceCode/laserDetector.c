#include <avr/io.h>
#include <avr/interrupt.h>

#define LASER_OUT_PIN       (1 << PB0)
#define LASER_SENSE_IN_PIN  (1 << PB3)

int gTimer0Count = 0;

// This should be called about about every 1/20 of a second.
ISR(TIMER0_COMPA_vect)
{
    // Just for testing reset the output once a second
    gTimer0Count++;
    if (gTimer0Count > 20) {
        PORTB &= ~LASER_OUT_PIN;
	gTimer0Count = 0;
    }
}

// When the laser is detected we turn on the led.
ISR(INT0_vect)
{
    PORTB |= LASER_OUT_PIN;
}

int 
main (void) {
  
    // Configure the "laser is on" output signal as an output, and all the
    // other pins as inputs.
    DDRB = LASER_OUT_PIN;

    // Make it so the input from the laser will use the internal
    // pull up resistor.  Other inputs will have no pullup, and the
    // outputs will all be low.
    PORTB = LASER_SENSE_IN_PIN;

    // Set timer 0 for CTC mode
    TCCR0B |= (1 << WGM02);

    // With a 1/1024 prescaler
    TCCR0B |= ((1 << CS00) | (1 << CS01));

    // Enable the CTC interrupt
    TIMSK |= (1 << OCIE0A);


    MCUCR = 1 << ISC01; // Trigger on falling edge.
    GIMSK = 1 << INT0;  // Enable external interupt INT0


    sei();

    // (1/target freq) / (prescale/1000000) - 1 and our target freq is 1/20 of a second so 
    // but even with a max 1024 prescaler the count is > 8 bits so we just use 255 to go as slow as we can.
    // 
    // No prescaler needed for this speed but we're getting close. Right now this is assuming laser pulses are coming
    // in at about 300 per second or more.  So we're just picking a time that's sure to have had pulses.
    
    OCR0A = 51;  

    for (;;) {
    }
}
