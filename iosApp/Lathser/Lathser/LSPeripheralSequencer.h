//
//  LSPeripheralSequencer.h
//  Lathser
//
//  Created by Kurt Schaefer on 5/9/15.
//  Copyright (c) 2015 Kurt Schaefer. All rights reserved.
//
//  I've had a hard time with too much info being sent to the Arduino in a lump
//  just silently failing.  This class deals with the sending the info in
//  individual lines and waiting for an acknowledgment/responce from the Arduino.  That may
//  keep the send buffer from overflowing.  Hopefully.  This also seprates responses to sends
//  from sends initiated from the arduino.  Responces must be of the form *<response>
//  and just * for a positive ack without responce.  This doesn't try to do anything fancy with
//  retrying/checksum's etc.  The hope is that this is enough to mostly work.

#import <Foundation/Foundation.h>
#import "UARTPeripheral.h"


typedef NS_ENUM(NSInteger, LSPeripheralConnectionState) {
    LSPeripheralConnectionStateNotConnected = 0,
    LSPeripheralConnectionStateScanning,
    LSPeripheralConnectionStateConnected,
};


@protocol LSPeripheralSequencerDelegate <NSObject>
- (void)didRecieveString:(NSString*)string;
- (void)connectionStateChanged:(LSPeripheralConnectionState)connectionState;
@end

@interface LSPeripheralSequencer : NSObject
@property (nonatomic, strong) UARTPeripheral* currentPeripheral;
@property (nonatomic, assign) LSPeripheralConnectionState connectionState;
@property (nonatomic, weak) id<LSPeripheralSequencerDelegate> delegate;

- (void)scanForPeripherals;
- (void)disconnect;

- (void)sendString:(NSString*)string
           success:(void (^)(NSString*responce))success
           failure:(void (^)(NSString*error))failure
           finally:(void (^)())finally;

- (void)sendStringArray:(NSArray*)stringArray
                success:(void (^)(NSString*responce))success
                failure:(void (^)(NSString*error))failure
                finally:(void (^)())finally;

@end
