import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { endpoint } = await request.json();
    
    // In production, you would:
    // 1. Find the subscription in the database by endpoint
    // 2. Delete it
    
    console.log('Push unsubscription received for:', endpoint);
    
    return NextResponse.json({
      success: true,
      message: 'Unsubscribed successfully',
    });
  } catch (error) {
    console.error('Error unsubscribing from push:', error);
    return NextResponse.json(
      { success: false, error: 'Failed to unsubscribe' },
      { status: 500 }
    );
  }
}
